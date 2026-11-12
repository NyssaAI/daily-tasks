"""Responsibility: Verify PlanningToolsDispatcher session routing, error parity, eviction, and workspace isolation.
Public interface:
+-- test_dispatcher_isolates_concurrent_sessions_across_workspaces_and_evicts_on_cancel(tmp_path)
+-- test_dispatcher_preserves_session_on_failed_confirm_and_evicts_only_on_success(tmp_path)
+-- test_dispatcher_rejects_blank_or_relative_workspace_root_even_with_default_workspace(tmp_path)
`-- test_dispatcher_session_id_error_parity(tmp_path, session_id, code)

Unit tests for `PlanningToolsDispatcher` across dynamic multi-workspace sessions.
"""

from __future__ import annotations

import asyncio
import json
import shutil
from datetime import UTC, datetime
from itertools import count
from pathlib import Path
from typing import Final
from uuid import UUID

import pytest

from daily_tasks.server.planning_tools_dispatcher import PlanningToolsDispatcher
from daily_tasks.server.types import ServerOverrides

_SPECS_ROOT: Final[Path] = Path(__file__).resolve().parents[4] / "docs" / "specs"
_NOW: Final = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)
_PROJECT: Final = "projects/2026.10.20-daily-tasks-mcp-server"
_MILESTONE: Final = f"{_PROJECT}/m2-planning-session-spike"
_TASK_ID: Final = "019a4b2c-1f00-7a10-8000-000000000003"


def _seed_workspace(root: Path, email: str = "jordan@example.com") -> Path:
    for relative, sample in (
        (f"{_PROJECT}/project-index.md", "5-sample-project-index.md"),
        (f"{_MILESTONE}/m2-planning-session-spike.md", "6-sample-milestone.md"),
        (f"{_MILESTONE}/t1-wire-gmail-connector.md", "4-sample-task.md"),
        (f"{_PROJECT}/blockers/b1-google-oauth-app-verification.md", "7-sample-blocker.md"),
    ):
        target = root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(_SPECS_ROOT / sample, target)
    (root / "daily-plans").mkdir(exist_ok=True)
    state_dir = root / ".nyssa-ai" / "daily-tasks"
    state_dir.mkdir(parents=True, exist_ok=True)
    (state_dir / "profile.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "user": {"name": "Jordan", "email": email},
                "timezone": "America/Chicago",
                "projectsRoot": "projects",
                "dailyPlansRelative": "daily-plans",
            }
        ),
        encoding="utf-8",
    )
    return root


def _dispatcher(
    default_workspace: Path | None = None,
    config_dir: Path | None = None,
) -> PlanningToolsDispatcher:
    numbers = count(1)
    return PlanningToolsDispatcher(
        overrides=ServerOverrides(workspace_root=default_workspace, config_dir=config_dir),
        clock=lambda: _NOW,
        new_id=lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}"),
    )


def test_dispatcher_rejects_blank_or_relative_workspace_root_even_with_default_workspace(tmp_path: Path) -> None:
    default_ws = _seed_workspace(tmp_path / "default_ws")
    dispatcher = _dispatcher(default_workspace=default_ws, config_dir=tmp_path / "config")

    blank = asyncio.run(dispatcher.start_session(workspace_root="   "))
    relative = dispatcher.get_fetch_window(workspace_root="relative/ws")

    assert (blank["status"], blank["code"]) == ("error", "Validation")
    assert "non-empty absolute path" in str(blank["message"])
    assert (relative["status"], relative["code"]) == ("error", "Validation")
    assert "absolute path" in str(relative["message"])


@pytest.mark.parametrize(
    ("session_id", "code"),
    [
        ("not-a-uuid", "Validation"),
        ("019a4b2c-9000-7000-8000-0000000000ff", "NotFound"),
    ],
)
def test_dispatcher_session_id_error_parity(
    tmp_path: Path,
    session_id: str,
    code: str,
) -> None:
    dispatcher = _dispatcher(config_dir=tmp_path / "config")

    state_reply = dispatcher.get_session_state(session_id)
    advance_reply = dispatcher.advance_screen(session_id, 2)
    ops_reply = dispatcher.execute_operations(session_id, "noop")
    confirm_reply = dispatcher.confirm_plan(session_id, True)
    cancel_reply = dispatcher.cancel_session(session_id)

    for reply in (state_reply, advance_reply, ops_reply, confirm_reply, cancel_reply):
        assert (reply["status"], reply["code"]) == ("error", code)


def test_dispatcher_preserves_session_on_failed_confirm_and_evicts_only_on_success(tmp_path: Path) -> None:
    ws = _seed_workspace(tmp_path / "ws")
    dispatcher = _dispatcher(config_dir=tmp_path / "config")

    started = asyncio.run(dispatcher.start_session(date="2026-11-03", workspace_root=str(ws)))
    assert started["status"] == "ok"
    session_id = str(started["session_id"])

    # Confirming before reaching Screen 3 returns status="refused" AND keeps the session alive
    refused_early = dispatcher.confirm_plan(session_id, True)
    assert (refused_early["status"], refused_early["expected_tool"]) == ("refused", "daily_tasks_advance_screen")
    assert dispatcher.get_session_state(session_id)["status"] == "ok"

    assert dispatcher.advance_screen(session_id, 2)["status"] == "ok"
    staged = dispatcher.execute_operations(
        session_id,
        "plan gmail task",
        operations=[
            {
                "kind": "assign-to-day",
                "row": 1,
                "item_type": "task",
                "item_id": _TASK_ID,
                "local_date": "2026-11-03",
            }
        ],
    )
    assert staged["status"] == "ok"
    assert dispatcher.advance_screen(session_id, 3)["status"] == "ok"

    # Confirming with confirmed=False on Screen 3 fails AND keeps the session alive
    unconfirmed = dispatcher.confirm_plan(session_id, False)
    assert (unconfirmed["status"], unconfirmed["code"]) == ("error", "Forbidden")
    assert dispatcher.get_session_state(session_id)["status"] == "ok"

    # Confirming with confirmed=True writes the plan and evicts the session
    confirmed = dispatcher.confirm_plan(session_id, True)
    assert confirmed["status"] == "ok"
    assert (ws / "daily-plans/2026.11.03-daily-plan.md").is_file()
    after_confirm = dispatcher.get_session_state(session_id)
    assert (after_confirm["status"], after_confirm["code"]) == ("error", "NotFound")


def test_dispatcher_isolates_concurrent_sessions_across_workspaces_and_evicts_on_cancel(tmp_path: Path) -> None:
    ws_a = _seed_workspace(tmp_path / "ws_a")
    ws_b = _seed_workspace(tmp_path / "ws_b")
    dispatcher = _dispatcher(config_dir=tmp_path / "config")

    start_a = asyncio.run(dispatcher.start_session(date="2026-11-03", workspace_root=str(ws_a)))
    start_b = asyncio.run(dispatcher.start_session(date="2026-11-03", workspace_root=str(ws_b)))
    id_a, id_b = str(start_a["session_id"]), str(start_b["session_id"])
    assert id_a != id_b

    assert dispatcher.cancel_session(id_a)["status"] == "ok"
    assert dispatcher.get_session_state(id_a)["code"] == "NotFound"
    assert dispatcher.get_session_state(id_b)["status"] == "ok"
