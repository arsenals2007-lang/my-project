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


def parse_command(text, environment=None):
    """Разобрать строку; одинарные кавычки запрещают раскрытие $NAME."""
    environment = os.environ if environment is None else environment
    tokens, buffer = [], []
    quote, active, position = None, False, 0
    while position < len(text):
        char = text[position]
        if char == "\\" and quote != "'":
            position += 1
            if position == len(text):
                raise ValueError("обратная косая черта без символа")
            buffer.append(text[position])
            active = True
        elif char in ("'", '"') and quote in (None, char):
            quote = None if quote == char else char
            active = True
        elif char.isspace() and quote is None:
            if active:
                tokens.append("".join(buffer))
                buffer, active = [], False
        elif char == "#" and quote is None:
            break
        elif char == "$" and quote != "'":
            value, position = expand_variable(text, position, environment)
            buffer.append(value)
            active = True
            continue
        else:
            buffer.append(char)
            active = True
        position += 1
    if quote is not None:
        raise ValueError("незакрытая кавычка")
    if active:
        tokens.append("".join(buffer))
    return tokens
