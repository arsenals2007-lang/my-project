"""Общие проверки аргументов команд."""


def parse_options(arguments, allowed=""):
    """Разобрать короткие флаги, их комбинации и разделитель --."""
    flags, paths = set(), []
    positional = False
    for argument in arguments:
        if argument == "--" and not positional:
            positional = True
        elif argument.startswith("-") and argument != "-" and not positional:
            letters = set(argument[1:])
            if not letters or letters - set(allowed):
                raise ValueError(f"неизвестная опция: {argument}")
            flags.update(letters)
        else:
            paths.append(argument)
    return flags, paths


def check_count(arguments, minimum, maximum, usage):
    """Проверить число аргументов и вывести ожидаемый синтаксис."""
    if not minimum <= len(arguments) <= maximum:
        raise ValueError(f"использование: {usage}")
