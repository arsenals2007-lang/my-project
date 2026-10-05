"""Проверки XML, base64, путей и неизменности источника."""

from pathlib import Path
import tempfile
import unittest

from shell18.vfs import VFS


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class VFSTests(unittest.TestCase):
    """Проверяет корректные и поврежденные источники VFS."""

    def test_load_binary_and_deep(self):
        """Бинарные данные декодируются, глубокие каталоги доступны."""
        vfs = VFS.load(EXAMPLES / "files.xml")
        self.assertEqual(vfs.nodes["/binary.bin"].data, bytes([0, 1, 2, 255]))
        vfs = VFS.load(EXAMPLES / "deep.xml")
        self.assertEqual(vfs.resolve("projects/demo", "/home/student"),
                         "/home/student/projects/demo")
        self.assertEqual(vfs.resolve("../../.."), "/")

    def test_invalid_formats(self):
        """Неверная схема, дубликаты, base64 и имена отвергаются."""
        samples = (
            "<broken>", "<wrong/>", '<vfs><file name="../x"/></vfs>',
            '<vfs><file name="x"/><file name="x"/></vfs>',
            '<vfs><file name="x" encoding="base64">!</file></vfs>',
            '<vfs><directory name="x">text</directory></vfs>',
            '<vfs><file name="x" encoding="unknown"/></vfs>',
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "vfs.xml"
            for sample in samples:
                path.write_text(sample, encoding="utf-8")
                with self.subTest(sample=sample), self.assertRaises(ValueError):
                    VFS.load(path)
            with self.assertRaises(ValueError):
                VFS.load(Path(directory) / "missing.xml")

    def test_intermediate_file_and_empty_path(self):
        """Нельзя проходить через файл, даже с последующим .. ."""
        vfs = VFS.load(EXAMPLES / "files.xml")
        for path in ("/hello.txt/../", "", "/missing"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                vfs.resolve(path)

    def test_source_unchanged(self):
        """Изменение объекта в памяти не затрагивает XML на диске."""
        path = EXAMPLES / "files.xml"
        original = path.read_bytes()
        vfs = VFS.load(path)
        vfs.nodes["/hello.txt"].owner = "other"
        self.assertEqual(path.read_bytes(), original)
