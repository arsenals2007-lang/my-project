"""Цикл чтения, исполнения и вывода результата команд."""

import getpass
import socket

from .parser import parse_command


class Shell:
    """Хранит состояние сеанса и выполняет команды эмулятора."""

    def __init__(self, output=print):
        """Настроить вывод и получить реальные имя пользователя и хост."""
        self.output = output
        self.username = getpass.getuser()
        self.hostname = socket.gethostname()
        self.running = True
        self.cwd = "/"

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
            if command == "exit":
                if arguments:
                    raise ValueError("exit: аргументы не поддерживаются")
                self.running = False
            elif command in ("ls", "cd"):
                if len(arguments) > 1:
                    raise ValueError(f"{command}: слишком много аргументов")
                self.output(f"{command}: {arguments!r}")
            else:
                raise ValueError(f"неизвестная команда: {command}")
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
