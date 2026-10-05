"""Цикл чтения, исполнения и вывода результата команд."""

import getpass
import socket

from .parser import parse_command
from .vfs import VFS
from .commands import Commands
from .mutations import Mutations


class Shell:
    """Хранит состояние сеанса и выполняет команды эмулятора."""

    def __init__(self, output=print, vfs=None):
        """Настроить вывод и получить реальные имя пользователя и хост."""
        self.output = output
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.running = True
        self.cwd = "/"
        self.vfs = VFS() if vfs is None else vfs
        self.previous = "/"
        self.commands = Commands(self)
        self.mutations = Mutations(self)
        self.handlers = {**self.commands.handlers, **self.mutations.handlers}

    def prompt(self):
        """Сформировать приглашение из данных ОС и текущего пути."""
        return f"{self.username}@{self.hostname}:{self.cwd}$ "

    def execute(self, line):
        """Выполнить строку; вернуть False при ошибке, True при успехе."""
        try:
            tokens = parse_command(line)
            if not tokens:
                return True
            command, *arguments = tokens
            handler = self.handlers.get(command)
            if handler is None:
                raise ValueError(f"неизвестная команда: {command}")
            handler(arguments)
            return True
        except ValueError as error:
            self.output(f"Ошибка: {error}")
            return False

    def repl(self):
        """Читать команды до exit или конца ввода; Ctrl+C отменяет ввод."""
        while self.running:
            try:
                line = input(self.prompt())
            except EOFError:
                break
            except KeyboardInterrupt:
                self.output("")
                continue
            self.execute(line)
