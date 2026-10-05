"""Виртуальная файловая система: загрузка XML, данные только в памяти."""

import base64
import binascii
from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class Node:
    """Каталог или файл с содержимым и виртуальными владельцем и группой."""

    directory: bool
    data: bytes = b""
    owner: str = "user"
    group: str = "users"


def validate_element(element):
    """Проверить имя, тип элемента и допустимые атрибуты схемы."""
    if element.tag not in ("directory", "file"):
        raise ValueError(f"неизвестный XML-элемент: {element.tag}")
    allowed = {"name", "owner", "group"}
    if element.tag == "file":
        allowed.add("encoding")
    if set(element.attrib) - allowed:
        raise ValueError("неизвестный атрибут узла VFS")
    name = element.get("name", "")
    if not name or name in (".", "..") or "/" in name or "\0" in name:
        raise ValueError(f"недопустимое имя узла: {name!r}")
    if not element.get("owner", "user") or not element.get("group", "users"):
        raise ValueError("владелец и группа не могут быть пустыми")
    return name


def file_data(element):
    """Прочитать UTF-8 или строго проверенный base64 без записи на диск."""
    if len(element):
        raise ValueError("файл не может содержать вложенные элементы")
    encoding = element.get("encoding", "utf-8")
    text = element.text or ""
    if encoding == "utf-8":
        return text.encode("utf-8")
    if encoding == "base64":
        try:
            return base64.b64decode("".join(text.split()), validate=True)
        except (ValueError, binascii.Error) as error:
            raise ValueError("некорректные данные base64") from error
    raise ValueError(f"неизвестная кодировка файла: {encoding}")


def load_children(vfs, parent, element):
    """Рекурсивно перенести элементы XML в словарь узлов VFS."""
    if element.text and element.text.strip():
        raise ValueError("каталог не должен содержать текст")
    for child in element:
        name = validate_element(child)
        path = parent.rstrip("/") + "/" + name
        if path in vfs.nodes:
            raise ValueError(f"повторяющийся путь: {path}")
        directory = child.tag == "directory"
        data = b"" if directory else file_data(child)
        vfs.nodes[path] = Node(
            directory, data, child.get("owner", "user"),
            child.get("group", "users")
        )
        if child.tail and child.tail.strip():
            raise ValueError("текст между узлами VFS не допускается")
        if directory:
            load_children(vfs, path, child)


class VFS:
    """Хранит виртуальные узлы в словаре абсолютных POSIX-путей."""

    def __init__(self, name="memory"):
        """Создать пустую VFS с корневым каталогом."""
        self.name = name
        self.nodes = {"/": Node(directory=True)}

    @classmethod
    def load(cls, path):
        """Прочитать UTF-8 XML и сообщить об ошибке файла или структуры."""
        try:
            text = Path(path).read_bytes().decode("utf-8-sig")
            if "<!DOCTYPE" in text.upper() or "<!ENTITY" in text.upper():
                raise ValueError("DTD и сущности в VFS не поддерживаются")
            root = ET.fromstring(text)
            if root.tag != "vfs" or set(root.attrib) - {"name"}:
                raise ValueError("ожидался корневой элемент <vfs name=...>")
            vfs = cls(root.get("name", Path(path).stem))
            load_children(vfs, "/", root)
            return vfs
        except (OSError, ValueError, ET.ParseError, RecursionError) as error:
            raise ValueError(f"загрузка VFS {path}: {error}") from error

    def resolve(self, path, cwd="/"):
        """Найти существующий путь, проверяя каждый промежуточный каталог."""
        if not path or "\0" in path:
            raise ValueError("пустой или некорректный путь")
        parts = [] if path.startswith("/") else cwd.strip("/").split("/")
        parts = [part for part in parts if part]
        for part in path.split("/"):
            self.walk_component(parts, part)
        return "/" + "/".join(parts)

    def walk_component(self, parts, part):
        """Обработать один компонент пути с проверкой типа родителя."""
        current = "/" + "/".join(parts)
        if not self.nodes[current].directory:
            raise ValueError(f"не каталог: {current}")
        if part in ("", "."):
            return
        if part == "..":
            if parts:
                parts.pop()
            return
        parts.append(part)
        candidate = "/" + "/".join(parts)
        if candidate not in self.nodes:
            raise ValueError(f"путь не найден: {candidate}")

    def children(self, path, show_hidden=True):
        """Вернуть отсортированные прямые дочерние пути каталога."""
        prefix = path.rstrip("/") + "/"
        return sorted(
            name for name in self.nodes
            if name.startswith(prefix) and name != path
            and "/" not in name[len(prefix):]
            and (show_hidden or not name[len(prefix):].startswith("."))
        )
