"""Проверки настоящего CLI, кодов выхода и стартовых файлов."""

import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]


def launch(*arguments, input_text=""):
    """Запустить отдельный процесс без интерактивного терминала."""
    environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"))
    return subprocess.run(
        [sys.executable, "-m", "shell18", *arguments],
        input=input_text, text=True, capture_output=True,
        cwd=ROOT, env=environment, timeout=10, check=False
    )


class CLITests(unittest.TestCase):
    """Проверяет интеграцию парсера запуска, загрузки VFS и скрипта."""

    def test_successful_demo(self):
        """Демонстрационный скрипт исполняет весь проект без ошибок."""
        original = (ROOT / "examples/deep.xml").read_bytes()
        result = launch("--vfs", "examples/deep.xml", "--script",
                        "examples/demo.shell", "--batch")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertIn("student students", result.stdout)
        self.assertIn("nested", result.stdout)
        self.assertEqual((ROOT / "examples/deep.xml").read_bytes(), original)

    def test_script_error_code_and_continuation(self):
        """Ошибка отмечает строку и код выхода, следующая команда работает."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "start.shell"
            path.write_text("unknown\npwd\nexit\n", encoding="utf-8")
            result = launch("--script", str(path), "--batch")
        self.assertEqual(result.returncode, 1)
        self.assertIn("строка 1", result.stdout)
        self.assertIn("$ pwd\n/\n", result.stdout)

    def test_invalid_sources(self):
        """Ошибки XML и стартового файла возвращают 1 и сообщение."""
        cases = (
            ("--vfs", "missing.xml"),
            ("--vfs", "examples/invalid.xml"),
            ("--script", "missing.shell"),
        )
        for arguments in cases:
            with self.subTest(arguments=arguments):
                result = launch(*arguments, "--batch")
                self.assertEqual(result.returncode, 1)
                self.assertIn("Ошибка", result.stderr)

    def test_batch_help_and_bad_options(self):
        """Пакетный режим не ждет ввода, справка и аргументы имеют коды."""
        self.assertEqual(launch("--batch").returncode, 0)
        result = launch("--help")
        self.assertEqual(result.returncode, 0)
        self.assertIn("--vfs", result.stdout)
        self.assertEqual(launch("--unknown").returncode, 2)

    def test_repl_input_and_eof(self):
        """Цикл принимает несколько команд и завершается на EOF."""
        result = launch(input_text="pwd\nmkdir /new\nls\n")
        self.assertEqual(result.returncode, 0)
        self.assertIn("$ /\n", result.stdout)
        self.assertIn("$ new\n", result.stdout)
