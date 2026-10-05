"""Регрессии глубокого дерева и проверки кодировки источника XML."""

from pathlib import Path
import sys
import tempfile
import unittest

from shell18.shell import Shell
from shell18.vfs import VFS


class EdgeCaseTests(unittest.TestCase):
    """Проверяет безопасный обход и отклонение неподдерживаемого XML."""

    def test_tree_deeper_than_recursion_limit(self):
        """Созданное через mkdir дерево не вызывает RecursionError."""
        output = []
        shell = Shell(output.append)
        depth = sys.getrecursionlimit() + 10
        path = "/" + "/".join(f"d{index}" for index in range(depth))
        self.assertTrue(shell.execute("mkdir -p " + path))
        self.assertTrue(shell.execute("tree"))
        self.assertEqual(len(output), depth + 1)
        self.assertTrue(output[-1].endswith(f"└── d{depth - 1}"))
        self.assertTrue(shell.execute("pwd"))

    def test_tree_keeps_depth_first_order(self):
        """После каталога выводятся его дети, затем следующий сосед."""
        output = []
        shell = Shell(output.append)
        self.assertTrue(shell.execute("mkdir -p /a/child /b/child"))
        self.assertTrue(shell.execute("tree"))
        self.assertEqual(output, [
            "/", "├── a", "│   └── child", "└── b", "    └── child"
        ])

    def test_xml_encoding_and_entities(self):
        """UTF-8 с BOM допустим; UTF-16 и объявления сущностей запрещены."""
        xml = '<vfs><file name="x">Текст</file></vfs>'
        dtd = (
            '<!DOCTYPE vfs [<!ENTITY data "expanded">]>'
            '<vfs><file name="x">&data;</file></vfs>'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xml"
            path.write_bytes(xml.encode("utf-8-sig"))
            self.assertEqual(VFS.load(path).nodes["/x"].data,
                             "Текст".encode("utf-8"))
            for contents in (xml.encode("utf-16"), dtd.encode("utf-16"),
                             dtd.encode("utf-8")):
                with self.subTest(contents=contents[:20]):
                    path.write_bytes(contents)
                    with self.assertRaises(ValueError):
                        VFS.load(path)
