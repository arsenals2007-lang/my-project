"""Команды изменения виртуальных узлов без операций записи на диск."""

import re

from .options import check_count, parse_options
from .vfs import Node


IDENTITY = re.compile(r"[A-Za-z0-9_.-]+\Z")


def ownership(specification):
    """Разобрать OWNER, OWNER:GROUP, :GROUP и OWNER:."""
    owner, separator, group = specification.partition(":")
    if separator and not group and owner:
        group = owner
    if not owner and not group:
        raise ValueError("chown: владелец или группа обязательны")
    validate_identity(owner, group)
    return owner or None, group or None


def validate_identity(owner, group):
    """Проверить синтаксис виртуальных владельца и группы."""
    for value in (owner, group):
        if value and not IDENTITY.fullmatch(value):
            raise ValueError(f"chown: недопустимое имя: {value!r}")


def directory_component(vfs, current, part, create, owner):
    """Найти или создать компонент, вернуть путь и признак существования."""
    if not vfs.nodes[current].directory:
        raise ValueError(f"mkdir: не каталог: {current}")
    if part in (".", ".."):
        return vfs.resolve(part, current), True
    candidate = current.rstrip("/") + "/" + part
    if candidate in vfs.nodes:
        if not vfs.nodes[candidate].directory:
            raise ValueError(f"mkdir: не каталог: {candidate}")
        return candidate, True
    if not create:
        raise ValueError(f"mkdir: родитель не найден: {candidate}")
    vfs.nodes[candidate] = Node(
        directory=True, owner=owner, group=vfs.nodes[current].group
    )
    return candidate, False


def make_directory(vfs, path, cwd, parents, owner):
    """Создать каталог; с parents создать недостающие промежуточные узлы."""
    if not path or "\0" in path:
        raise ValueError("mkdir: пустой или некорректный путь")
    current = "/" if path.startswith("/") else cwd
    components = [part for part in path.split("/") if part]
    last_index = len(components) - 1
    existed = True
    for index, part in enumerate(components):
        create = parents or index == last_index
        current, existed = directory_component(
            vfs, current, part, create, owner
        )
    if existed and not parents:
        raise ValueError(f"mkdir: каталог уже существует: {current}")


class Mutations:
    """Обработчики mkdir и chown для текущего сеанса."""

    def __init__(self, shell):
        """Привязать обработчики к виртуальной ФС и текущему пути."""
        self.shell = shell
        self.handlers = {"mkdir": self.mkdir, "chown": self.chown}

    def mkdir(self, arguments):
        """Создать один или несколько каталогов; -p включает родителей."""
        flags, paths = parse_options(arguments, "p")
        check_count(paths, 1, len(paths), "mkdir [-p] путь [путь ...]")
        for path in paths:
            make_directory(
                self.shell.vfs, path, self.shell.cwd,
                "p" in flags, self.shell.username
            )

    def chown(self, arguments):
        """Изменить владельца/группу; -R применяется ко всем потомкам."""
        flags, paths = parse_options(arguments, "R")
        check_count(paths, 2, len(paths),
                    "chown [-R] владелец[:группа] путь [путь ...]")
        owner, group = ownership(paths[0])
        vfs = self.shell.vfs
        for path in paths[1:]:
            resolved = vfs.resolve(path, self.shell.cwd)
            prefix = resolved.rstrip("/") + "/"
            targets = [resolved]
            if "R" in flags:
                targets.extend(name for name in vfs.nodes
                               if name != resolved and name.startswith(prefix))
            for name in targets:
                node = vfs.nodes[name]
                if owner is not None:
                    node.owner = owner
                if group is not None:
                    node.group = group
