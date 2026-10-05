"""Проверки разбора ввода и раскрытия переменных."""

import unittest

from shell18.parser import parse_command


class ParserTests(unittest.TestCase):
    """Проверяет кавычки, экранирование и ошибочные строки."""

    def test_environment_and_quotes(self):
        """Переменные раскрываются вне одинарных кавычек."""
        env = {"HOME": "/home/a b"}
        self.assertEqual(
            parse_command('cd "$HOME"', env), ["cd", "/home/a b"]
        )
        self.assertEqual(parse_command("cd '$HOME'", env), ["cd", "$HOME"])
        self.assertEqual(parse_command("cd ${HOME}", env), ["cd", "/home/a b"])

    def test_empty_escaped_and_adjacent(self):
        """Пустые аргументы и соседние фрагменты сохраняются."""
        self.assertEqual(parse_command('ls ""'), ["ls", ""])
        self.assertEqual(parse_command(r"ls a\ b"), ["ls", "a b"])
        self.assertEqual(parse_command('ls a"b c"'), ["ls", "ab c"])
        self.assertEqual(parse_command(r"ls \$HOME"), ["ls", "$HOME"])
        self.assertEqual(parse_command("  "), [])

    def test_invalid_input(self):
        """Незакрытые кавычки и обрыв экранирования дают ошибку."""
        for text in ('ls "abc', "cd '", "ls \\"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                parse_command(text)

    def test_values_are_data(self):
        """Кавычки и # из окружения не меняют синтаксис команды."""
        env = {"VALUE": 'a b # " cd /other'}
        self.assertEqual(parse_command("ls $VALUE", env),
                         ["ls", env["VALUE"]])
        self.assertEqual(parse_command('ls "$MISSING"', {}), ["ls", ""])
        self.assertEqual(parse_command(r'ls "a\q"'), ["ls", r"a\q"])
