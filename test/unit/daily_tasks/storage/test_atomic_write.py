# Responsibility: Prove atomic_write replaces file bytes completely and leaves no temp files behind.
# Public interface:
# (none)
"""Atomic replacement of a file through a synced sibling temp file."""

from pathlib import Path

import pytest

from daily_tasks.storage.atomic_write import atomic_write


def test_atomic_write_existing_file_replaces_bytes_and_cleans_up(tmp_path: Path) -> None:
    target = tmp_path / "record.md"
    target.write_bytes(b"old\r\n")

    atomic_write(target, b"new\r\ncontent\r\n")

    assert target.read_bytes() == b"new\r\ncontent\r\n"
    assert [p.name for p in tmp_path.iterdir()] == ["record.md"]


def test_atomic_write_missing_parent_creates_directories(tmp_path: Path) -> None:
    target = tmp_path / "a" / "b" / "state.json"

    atomic_write(target, b"{}")

    assert target.read_bytes() == b"{}"


def test_atomic_write_target_is_directory_raises_and_cleans_up(tmp_path: Path) -> None:
    (tmp_path / "taken").mkdir()

    with pytest.raises(OSError):
        atomic_write(tmp_path / "taken", b"data")

    assert [p.name for p in tmp_path.iterdir()] == ["taken"]
