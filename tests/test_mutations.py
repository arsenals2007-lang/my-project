"""Проверки mkdir, chown и изменения состояния только в памяти."""

from pathlib import Path
import tempfile
import unittest

from shell18.shell import Shell
from shell18.vfs import VFS


EXAMPLES = Path(__file__).resolve().parents[1] / "examples"


class MutationTests(unittest.TestCase):
    """Проверяет все режимы изменения узлов и сохранность источника."""

    def setUp(self):
        """Загрузить свежую VFS для каждого теста."""
        self.output = []
        self.shell = Shell(self.output.append, VFS.load(EXAMPLES / "deep.xml"))

    def test_mkdir_modes(self):
        """Создаются каталоги, родители, пути с пробелами и дефисом."""
        for line in ("mkdir /new /second", "cd /new", "mkdir child",
                     "mkdir -p a/b/c", "mkdir -p a/b/c",
                     'mkdir "with spaces"', "mkdir -- -dash"):
            self.assertTrue(self.shell.execute(line), self.output)
        self.assertIn("/new/a/b/c", self.shell.vfs.nodes)
        self.assertIn("/new/with spaces", self.shell.vfs.nodes)
        self.assertIn("/new/-dash", self.shell.vfs.nodes)
        self.assertEqual(self.shell.vfs.nodes["/new"].owner,
                         self.shell.username)

    def test_chown_modes(self):
        """Можно менять владельца, группу, обоих и рекурсивное поддерево."""
        self.assertTrue(self.shell.execute("chown alice /etc/config.txt"))
        node = self.shell.vfs.nodes["/etc/config.txt"]
        self.assertEqual((node.owner, node.group), ("alice", "users"))
        self.shell.execute("chown :staff /etc/config.txt")
        self.assertEqual((node.owner, node.group), ("alice", "staff"))
        self.shell.execute("chown bob: /etc/config.txt")
        self.assertEqual((node.owner, node.group), ("bob", "bob"))
        self.shell.execute("chown -R student:students /home")
        for path, node in self.shell.vfs.nodes.items():
            if path == "/home" or path.startswith("/home/"):
                self.assertEqual((node.owner, node.group),
                                 ("student", "students"))
        self.assertEqual(self.shell.vfs.nodes["/etc"].owner, "user")

    def test_invalid_mutations(self):
        """Невалидные команды не создают лишние виртуальные узлы."""
        original = set(self.shell.vfs.nodes)
        for line in ("mkdir", "mkdir /home", "mkdir /missing/child",
                     "mkdir /etc/config.txt/child", 'mkdir ""',
                     "mkdir -z /bad", "chown", "chown alice /missing",
                     "chown alice:staff:extra /home", "chown : /home",
                     "chown -z alice /home"):
            with self.subTest(line=line):
                self.assertFalse(self.shell.execute(line))
                self.assertEqual(set(self.shell.vfs.nodes), original)

    def test_only_memory_changes(self):
        """XML и реальный каталог не меняются после mkdir/chown."""
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.xml"
            original = (EXAMPLES / "deep.xml").read_bytes()
            path.write_bytes(original)
            shell = Shell(self.output.append, VFS.load(path))
            before = set(Path(directory).iterdir())
            self.assertTrue(shell.execute("mkdir -p /created/in/memory"))
            self.assertTrue(shell.execute("chown -R alice:staff /"))
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(set(Path(directory).iterdir()), before)
            reloaded = VFS.load(path)
            self.assertNotIn("/created", reloaded.nodes)
            self.assertEqual(reloaded.nodes["/"].owner, "user")
