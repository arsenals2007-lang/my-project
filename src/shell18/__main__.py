"""Точка входа: python -m shell18."""

import argparse
import sys

from .shell import Shell
from .startup import run_script


def read_options(argv):
    """Разобрать пути VFS, стартового скрипта и пакетный режим."""
    parser = argparse.ArgumentParser(description="Эмулятор: вариант 18")
    parser.add_argument("--vfs", help="путь к XML виртуальной ФС")
    parser.add_argument("--script", help="путь к стартовому скрипту")
    parser.add_argument(
        "--batch", action="store_true", help="не входить в REPL"
    )
    return parser.parse_args(argv)


def main(argv=None):
    """Показать настройки, выполнить скрипт и запустить REPL."""
    options = read_options(argv)
    print(f"[config] vfs={options.vfs!r}")
    print(f"[config] script={options.script!r}")
    print(f"[config] batch={options.batch}")
    shell = Shell()
    try:
        success = run_script(shell, options.script)
    except (OSError, UnicodeError) as error:
        print(f"Ошибка чтения скрипта: {error}", file=sys.stderr)
        return 1
    if shell.running and not options.batch:
        shell.repl()
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
