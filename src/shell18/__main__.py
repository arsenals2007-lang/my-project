"""Точка входа: python -m shell18."""

from .shell import Shell


def main():
    """Запустить интерактивный эмулятор."""
    Shell().repl()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
