"""Основные команды эмулятора; доступ только к виртуальным узлам."""

import calendar
from datetime import date

from .options import check_count, parse_options


MIN_YEAR, MAX_YEAR = 1, 9999
MIN_MONTH, MAX_MONTH = 1, 12


class Commands:
    """Реализует команды и предоставляет таблицу диспетчеризации."""

    def __init__(self, shell):
        """Связать команды с состоянием текущего сеанса."""
        self.shell = shell
        self.handlers = {
            "ls": self.ls, "cd": self.cd, "tree": self.tree,
            "cal": self.cal, "pwd": self.pwd, "exit": self.exit,
        }

    def exit(self, arguments):
        """Завершить сеанс без дополнительных аргументов."""
        check_count(arguments, 0, 0, "exit")
        self.shell.running = False

    def pwd(self, arguments):
        """Напечатать абсолютный путь текущего виртуального каталога."""
        check_count(arguments, 0, 0, "pwd")
        self.shell.output(self.shell.cwd)

    def cd(self, arguments):
        """Перейти в каталог; без пути — в /, '-' — в прошлый каталог."""
        _, paths = parse_options(arguments)
        check_count(paths, 0, 1, "cd [путь|-]")
        path = paths[0] if paths else "/"
        previous = path == "-"
        path = self.shell.previous if previous else path
        resolved = self.shell.vfs.resolve(path, self.shell.cwd)
        if not self.shell.vfs.nodes[resolved].directory:
            raise ValueError(f"cd: не каталог: {path}")
        self.shell.previous, self.shell.cwd = self.shell.cwd, resolved
        if previous:
            self.shell.output(resolved)

    def ls(self, arguments):
        """Показать каталог или файл; -a включает скрытые, -l метаданные."""
        flags, paths = parse_options(arguments, "al")
        check_count(paths, 0, 1, "ls [-a] [-l] [путь]")
        path = self.shell.vfs.resolve(
            paths[0] if paths else ".", self.shell.cwd
        )
        vfs = self.shell.vfs
        nodes = vfs.children(path, "a" in flags) if (
            vfs.nodes[path].directory
        ) else [path]
        for name in nodes:
            label = name.rsplit("/", 1)[-1]
            if "l" in flags:
                node = vfs.nodes[name]
                kind = "d" if node.directory else "-"
                label = (
                    f"{kind} {node.owner} {node.group} "
                    f"{len(node.data):>6} {label}"
                )
            self.shell.output(label)

    def tree(self, arguments):
        """Показать дерево от пути; -a включает скрытые узлы."""
        flags, paths = parse_options(arguments, "a")
        check_count(paths, 0, 1, "tree [-a] [путь]")
        path = self.shell.vfs.resolve(
            paths[0] if paths else ".", self.shell.cwd
        )
        self.shell.output(path)
        self.print_tree(path, "", "a" in flags)

    def print_tree(self, path, prefix, show_hidden):
        """Рекурсивно вывести дочерние узлы с соединительными линиями."""
        vfs = self.shell.vfs
        if not vfs.nodes[path].directory:
            return
        children = vfs.children(path, show_hidden)
        last_index = len(children) - 1
        for index, name in enumerate(children):
            last = index == last_index
            branch = "└── " if last else "├── "
            self.shell.output(prefix + branch + name.rsplit("/", 1)[-1])
            extension = "    " if last else "│   "
            self.print_tree(name, prefix + extension, show_hidden)

    def cal(self, arguments):
        """Вывести текущий месяц, весь год или указанный месяц и год."""
        check_count(arguments, 0, 2, "cal [год] | cal месяц год")
        today = date.today()
        values = [int(value) for value in arguments]
        year = values[-1] if values else today.year
        month = values[0] if len(values) == 2 else today.month
        if not MIN_YEAR <= year <= MAX_YEAR:
            raise ValueError("cal: год должен быть от 1 до 9999")
        if not MIN_MONTH <= month <= MAX_MONTH:
            raise ValueError("cal: месяц должен быть от 1 до 12")
        printer = calendar.TextCalendar(firstweekday=calendar.MONDAY)
        rendered = printer.formatyear(year) if len(values) == 1 else (
            printer.formatmonth(year, month)
        )
        self.shell.output(rendered.rstrip())
