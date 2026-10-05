"""Проверки основных команд, путей и ошибочных аргументов."""

import calendar
from datetime import date
from pathlib import Path
import unittest

from shell18.shell import Shell
from shell18.vfs import VFS


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class CommandTests(unittest.TestCase):
    """Проверяет поведение команд на многоуровневой VFS."""

    def setUp(self):
        """Загрузить новый независимый сеанс."""
        self.output = []
        self.shell = Shell(self.output.append, VFS.load(EXAMPLES / "deep.xml"))

    def test_ls_and_hidden_metadata(self):
        """Скрытые файлы видны с -a, владелец виден с -l."""
        self.assertTrue(self.shell.execute("ls"))
        self.assertNotIn(".hidden", self.output)
        self.output.clear()
        self.assertTrue(self.shell.execute("ls -al /home"))
        self.assertTrue(any("student students" in x for x in self.output))
        self.output.clear()
        self.shell.execute("ls -a")
        self.assertIn(".hidden", self.output)
        self.output.clear()
        self.shell.execute("ls /etc/config.txt")
        self.assertEqual(self.output, ["config.txt"])

    def test_navigation(self):
        """cd работает с пробелами, .., корнем и предыдущим каталогом."""
        for line in ('cd "folder with spaces"', "cd ..", "cd /home/student"):
            self.assertTrue(self.shell.execute(line))
        self.assertEqual(self.shell.cwd, "/home/student")
        self.assertTrue(self.shell.execute("cd -"))
        self.assertEqual(self.shell.cwd, "/")
        self.assertFalse(self.shell.execute("cd /etc/config.txt"))
        self.assertEqual(self.shell.cwd, "/")
        self.assertTrue(self.shell.execute("cd"))

    def test_tree(self):
        """Дерево содержит глубокий файл и скрытые узлы с -a."""
        self.assertTrue(self.shell.execute("tree -a"))
        self.assertTrue(any("readme.txt" in line for line in self.output))
        self.assertTrue(any(".hidden" in line for line in self.output))
        self.output.clear()
        self.assertTrue(self.shell.execute("tree /etc/config.txt"))
        self.assertEqual(self.output, ["/etc/config.txt"])

    def test_calendar(self):
        """Календарь совпадает со стандартной библиотекой, включая 29.02."""
        printer = calendar.TextCalendar(firstweekday=calendar.MONDAY)
        today = date.today()
        cases = (
            ("cal", printer.formatmonth(today.year, today.month)),
            ("cal 2 2024", printer.formatmonth(2024, 2)),
            ("cal 2026", printer.formatyear(2026)),
        )
        for line, expected in cases:
            self.output.clear()
            self.assertTrue(self.shell.execute(line))
            self.assertEqual(self.output, [expected.rstrip()])

    def test_invalid_arguments(self):
        """Неверные флаги, пути, даты и лишние аргументы дают ошибки."""
        for line in ("ls -z", "ls a b", "pwd extra", "tree -z",
                     "cd /missing", "cal 0 2026", "cal 13 2026",
                     "cal 0", "cal 10000", "cal text", "cal 1 2 3"):
            with self.subTest(line=line):
                self.assertFalse(self.shell.execute(line))
