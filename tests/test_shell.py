"""Проверки прототипа REPL."""

import unittest

from shell18.shell import Shell


class ShellTests(unittest.TestCase):
    """Проверяет команды, ошибки и завершение сеанса."""

    def setUp(self):
        """Перехватить вывод каждого тестового сеанса."""
        self.output = []
        self.shell = Shell(output=self.output.append)

    def test_stubs(self):
        """Заглушки показывают имя команды и аргументы."""
        self.assertTrue(self.shell.execute('ls "a b"'))
        self.assertEqual(self.output, ["ls: ['a b']"])

    def test_errors_keep_session_alive(self):
        """Ошибка не завершает интерактивный сеанс."""
        for line in ("unknown", "cd a b", "exit extra", 'ls "'):
            self.assertFalse(self.shell.execute(line))
            self.assertTrue(self.shell.running)

    def test_exit_and_prompt(self):
        """Приглашение содержит данные ОС, exit завершает сеанс."""
        self.assertIn(self.shell.username, self.shell.prompt())
        self.assertIn(self.shell.hostname, self.shell.prompt())
        self.assertTrue(self.shell.execute("exit"))
        self.assertFalse(self.shell.running)
