# Responsibility: List the Markdown files under a vault root, skipping attachment and trash folders.
# Public interface:
# +-- SKIPPED_DIRECTORIES
# `-- markdown_record_files(root)
"""Deterministic recursive discovery of `*.md` files below a Markdown vault root."""

import os
from pathlib import Path, PurePosixPath
from typing import Final

SKIPPED_DIRECTORIES: Final = frozenset({"inputs", "outputs", ".trash"})


def markdown_record_files(root: Path) -> tuple[PurePosixPath, ...]:
    """Return root-relative POSIX paths of every `*.md` file, sorted.

    Folders named in `SKIPPED_DIRECTORIES` and other hidden folders are not entered. Raises `OSError`
    when `root` itself cannot be listed; unreadable sub-folders are skipped.
    """
    with os.scandir(root):
        pass
    found: list[PurePosixPath] = []
    for directory, folders, files in os.walk(root):
        folders[:] = sorted(f for f in folders if f not in SKIPPED_DIRECTORIES and not f.startswith("."))
        relative = PurePosixPath(Path(directory).relative_to(root).as_posix())
        found.extend(relative / name for name in files if name.endswith(".md"))
    return tuple(sorted(found))
