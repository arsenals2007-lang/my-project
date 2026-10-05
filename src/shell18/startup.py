"""Исполнение стартового скрипта с отображением диалога."""

from pathlib import Path


def run_script(shell, path):
    """Показать ввод и вывод; сообщать номер ошибки и продолжать скрипт."""
    if path is None:
        return True
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    success = True
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        shell.output(shell.prompt() + line)
        if not shell.execute(line):
            shell.output(f"Ошибка скрипта {path}, строка {number}")
            success = False
        if not shell.running:
            break
    return success
