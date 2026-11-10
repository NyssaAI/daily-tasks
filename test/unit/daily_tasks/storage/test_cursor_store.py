"""Responsibility: Prove CursorStore persists fetch cursors atomically and reloads them unchanged.
Public interface:
+-- test_cursor_store_failed_replace_keeps_previous_file_and_no_temp(tmp_path, monkeypatch)
+-- test_cursor_store_malformed_file_fails_with_validation(tmp_path, content, log_capture)
+-- test_cursor_store_missing_file_returns_empty_cursors_for_workspace(tmp_path)
+-- test_cursor_store_relative_state_root_is_rejected()
+-- test_cursor_store_save_replaces_previous_file(tmp_path)
`-- test_cursor_store_save_then_load_round_trips_spec_example(tmp_path)

Fetch cursor persistence under a temporary `.nyssa-ai/daily-tasks/` state root.
"""

import os
from datetime import UTC, datetime
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok
from pydantic import TypeAdapter

from conftest import LogCapture, load_spec
from daily_tasks.domain import FetchCursor, FetchCursors
from daily_tasks.storage.cursor_store import CursorStore


def _state_root(tmp_path: Path) -> Path:
    return tmp_path / "vault" / ".nyssa-ai" / "daily-tasks"


def _spec_cursors() -> FetchCursors:
    return TypeAdapter(FetchCursors).validate_python(load_spec("fetch-cursors.json"))


def test_cursor_store_save_then_load_round_trips_spec_example(tmp_path: Path) -> None:
    store = CursorStore(_state_root(tmp_path), "D:/vaults/work")
    cursors = _spec_cursors()

    saved = store.save(cursors)
    loaded = store.load()

    assert isinstance(saved, Ok)
    assert isinstance(loaded, Ok)
    assert loaded.value == cursors
    assert store.path == _state_root(tmp_path) / "fetch-cursors.json"
    assert sorted(p.name for p in store.path.parent.iterdir()) == ["fetch-cursors.json"]


def test_cursor_store_save_replaces_previous_file(tmp_path: Path) -> None:
    store = CursorStore(_state_root(tmp_path), "/vault")
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
    store = CursorStore(_state_root(tmp_path), "/vault")

    loaded = store.load()

    assert isinstance(loaded, Ok)
    assert loaded.value == FetchCursors(workspace_root="/vault", cursors={})


@pytest.mark.parametrize(
    "content", ["{not json", '{"workspace_root": "/vault"}', '{"workspace_root": "/v", "cursors": {}, "x": 1}']
)
def test_cursor_store_malformed_file_fails_with_validation(
    tmp_path: Path, content: str, log_capture: LogCapture
) -> None:
    root = _state_root(tmp_path)
    root.mkdir(parents=True)
    (root / "fetch-cursors.json").write_text(content, encoding="utf-8")

    loaded = CursorStore(root, "/vault").load()

    assert isinstance(loaded, Err)
    assert str(loaded.category) == "Validation"
    assert log_capture.records[-1][0] == "error"


def test_cursor_store_failed_replace_keeps_previous_file_and_no_temp(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    store = CursorStore(_state_root(tmp_path), "D:/vaults/work")
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
        CursorStore(Path(".nyssa-ai/daily-tasks"), "/vault")
