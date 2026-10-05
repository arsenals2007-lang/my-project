"""Разбор кавычек и переменных без выполнения команд реальной ОС."""

import os
import re


VARIABLE = re.compile(r"\$(?:\{([A-Za-z_]\w*)\}|([A-Za-z_]\w*))")


def expand_variable(text, position, environment):
    """Вернуть значение переменной и позицию после ее имени."""
    match = VARIABLE.match(text, position)
    if match is None:
        return "$", position + 1
    name = match.group(1) or match.group(2)
    return environment.get(name, ""), match.end()


class Lexer:
    """Посимвольный разбор с сохранением состояния кавычек."""

    def __init__(self, text, environment):
        """Подготовить строку, окружение и буфер текущего аргумента."""
        self.text = text
        self.environment = environment
        self.position = 0
        self.quote = None
        self.active = False
        self.buffer = []
        self.tokens = []

    def append(self, value):
        """Добавить фрагмент к аргументу, включая пустые значения."""
        self.buffer.append(value)
        self.active = True

    def flush(self):
        """Закончить аргумент, если ввод уже начат."""
        if self.active:
            self.tokens.append("".join(self.buffer))
            self.buffer, self.active = [], False

    def change_quote(self, char):
        """Открыть/закрыть кавычки или сохранить кавычку другого типа."""
        self.active = True
        if self.quote is None:
            self.quote = char
        elif self.quote == char:
            self.quote = None
        else:
            self.append(char)

    def escape(self):
        """Прочитать экранированный символ с учетом двойных кавычек."""
        self.position += 1
        if self.position == len(self.text):
            raise ValueError("обратная косая черта без символа")
        char = self.text[self.position]
        if self.quote == '"' and char not in '$"\\':
            self.append("\\")
        self.append(char)

    def step(self):
        """Обработать текущий символ и перейти к следующему."""
        char = self.text[self.position]
        if self.quote == "'":
            if char == "'":
                self.quote = None
            else:
                self.append(char)
        elif char == "\\":
            self.escape()
        elif char in ("'", '"'):
            self.change_quote(char)
        elif self.quote is None and char.isspace():
            self.flush()
        elif self.quote is None and char == "#":
            self.position = len(self.text)
            return
        elif char == "$":
            value, end = expand_variable(
                self.text, self.position, self.environment
            )
            self.append(value)
            self.position = end - 1
        else:
            self.append(char)
        self.position += 1


def parse_command(text, environment=None):
    """Разобрать строку; одинарные кавычки запрещают раскрытие $NAME."""
    environment = os.environ if environment is None else environment
    lexer = Lexer(text, environment)
    while lexer.position < len(text):
        lexer.step()
    if lexer.quote is not None:
        raise ValueError("незакрытая кавычка")
    lexer.flush()
    return lexer.tokens
