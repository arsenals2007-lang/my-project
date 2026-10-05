"""Проверки исполнения скриптов и комментариев."""

from pathlib import Path
import tempfile
import unittest

from shell18.parser import parse_command
from shell18.shell import Shell
from shell18.startup import run_script


class StartupTests(unittest.TestCase):
    """Проверяет продолжение после ошибки и номер строки."""

    def test_comments(self):
        """Символ # в кавычках или после обратной косой сохраняется."""
        self.assertEqual(parse_command('ls "#file" # comment'),
                         ["ls", "#file"])
        self.assertEqual(parse_command(r"ls \#file"), ["ls", "#file"])

    def test_transcript_errors_and_exit(self):
        """Скрипт показывает ввод, продолжает после ошибки, уважает exit."""
        output = []
        shell = Shell(output=output.append)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.shell"
            path.write_text("# comment\nunknown\nls\nexit\nunknown\n",
                            encoding="utf-8")
            self.assertFalse(run_script(shell, path))
        self.assertTrue(any("строка 2" in line for line in output))
        self.assertTrue(any(line.endswith("$ ls") for line in output))
        self.assertEqual(sum("$ unknown" in line for line in output), 1)
        self.assertFalse(shell.running)
