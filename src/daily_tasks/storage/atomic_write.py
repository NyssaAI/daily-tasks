# Responsibility: Replace one file's bytes atomically so readers never observe a partial write.
# Public interface:
# `-- atomic_write(path, data)
"""Temp file in the target directory, fsync, then `os.replace`; parent directories are created."""

import contextlib
import os
import tempfile
from pathlib import Path


def atomic_write(path: Path, data: bytes) -> None:
    """Write `data` to `path` through a synced sibling temp file and an atomic rename.

    Raises `OSError` on I/O failure; the temp file is removed and `path` keeps its previous bytes.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_name, path)
    except BaseException:
        with contextlib.suppress(FileNotFoundError):
            os.unlink(temp_name)
        raise
    _sync_directory(path.parent)


def _sync_directory(directory: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)
