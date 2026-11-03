# Responsibility: Prove CursorStore persists fetch cursors atomically and reloads them unchanged.
# Public interface:
# (none)
"""Fetch cursor persistence under a temporary `.nyssa-ai/daily-tasks/` state root."""

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok
from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import FetchCursor, FetchCursors
from daily_tasks.storage.cursor_store import CursorStore


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


def _state_root(tmp_path: Path) -> Path:
    return tmp_path / "vault" / ".nyssa-ai" / "daily-tasks"


def _spec_cursors() -> FetchCursors:
    return TypeAdapter(FetchCursors).validate_python(load_spec("fetch-cursors.json"))


def test_cursor_store_save_then_load_round_trips_spec_example(tmp_path: Path) -> None:
    store = CursorStore(_state_root(tmp_path), "D:/vaults/work", _RecordingLogger())
    cursors = _spec_cursors()

    saved = store.save(cursors)
    loaded = store.load()

    assert isinstance(saved, Ok)
    assert isinstance(loaded, Ok)
    assert loaded.value == cursors
    assert store.path == _state_root(tmp_path) / "fetch-cursors.json"
    assert sorted(p.name for p in store.path.parent.iterdir()) == ["fetch-cursors.json"]


def test_cursor_store_save_replaces_previous_file(tmp_path: Path) -> None:
    store = CursorStore(_state_root(tmp_path), "/vault", _RecordingLogger())
    store.save(_spec_cursors())
    moment = datetime(2026, 11, 4, 8, 0, tzinfo=UTC)
    updated = FetchCursors(
        workspace_root="/vault",
        cursors={
            "slack": FetchCursor(
                since=moment, last_external_id="C1:1", last_run_at=moment, last_status="ok", last_error=None
            )
        },
    )

    store.save(updated)

    loaded = store.load()
    assert isinstance(loaded, Ok)
    assert loaded.value == updated


def test_cursor_store_missing_file_returns_empty_cursors_for_workspace(tmp_path: Path) -> None:
    store = CursorStore(_state_root(tmp_path), "/vault", _RecordingLogger())

    loaded = store.load()

    assert isinstance(loaded, Ok)
    assert loaded.value == FetchCursors(workspace_root="/vault", cursors={})


@pytest.mark.parametrize(
    "content", ["{not json", '{"workspace_root": "/vault"}', '{"workspace_root": "/v", "cursors": {}, "x": 1}']
)
def test_cursor_store_malformed_file_fails_with_validation(tmp_path: Path, content: str) -> None:
    root = _state_root(tmp_path)
    root.mkdir(parents=True)
    (root / "fetch-cursors.json").write_text(content, encoding="utf-8")
    logger = _RecordingLogger()

    loaded = CursorStore(root, "/vault", logger).load()

    assert isinstance(loaded, Err)
    assert str(loaded.category) == "Validation"
    assert logger.records[-1][0] == "error"


def test_cursor_store_failed_replace_keeps_previous_file_and_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CursorStore(_state_root(tmp_path), "D:/vaults/work", _RecordingLogger())
    store.save(_spec_cursors())
    before = store.path.read_bytes()

    def _fail_replace(src: str, dst: Path) -> None:
        raise OSError("disk full")

    monkeypatch.setattr(os, "replace", _fail_replace)
    result = store.save(FetchCursors(workspace_root="D:/vaults/work", cursors={}))

    assert isinstance(result, Err)
    assert str(result.category) == "Unavailable"
    assert store.path.read_bytes() == before
    assert sorted(p.name for p in store.path.parent.iterdir()) == ["fetch-cursors.json"]


def test_cursor_store_relative_state_root_is_rejected() -> None:
    with pytest.raises(ValueError, match="absolute"):
        CursorStore(Path(".nyssa-ai/daily-tasks"), "/vault", _RecordingLogger())
