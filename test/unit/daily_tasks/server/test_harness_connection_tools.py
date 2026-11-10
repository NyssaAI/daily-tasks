"""Responsibility: Prove the MCP fetch-window tool and host-supplied message ingestion share the saved cursors.
Public interface:
+-- ARGV
+-- BLOCKER_ID
+-- MILESTONE
+-- NOW
+-- PROJECT
+-- test_cli_non_positive_initial_lookback_exits_2(tmp_path, days, capsys)
+-- test_get_fetch_window_custom_lookback_bounds_first_pull(tmp_path, profile, extra, days)
+-- test_get_fetch_window_first_pull_defaults_to_7_days(tmp_path)
+-- test_get_fetch_window_subsequent_pull_uses_saved_cursor(tmp_path)
+-- test_start_session_harness_messages_suggest_and_advance_cursor_on_confirm(tmp_path)
`-- test_start_session_rejects_malformed_harness_message(tmp_path)

`daily-tasks-mcp` over in-memory stdio: `daily_tasks_get_fetch_window` and `start_session(messages=...)`.
"""

import asyncio
import io
import json
import shutil
from datetime import UTC, datetime, timedelta
from itertools import count
from pathlib import Path
from uuid import UUID

import pytest
from pydantic import JsonValue

from conftest import SPECS_ROOT
from daily_tasks.cli import cli
from daily_tasks.domain import GraphUser
from daily_tasks.server import MarkdownWorkspaceReader, McpServer, PlanningTools, ServerSettings
from daily_tasks.storage.cursor_store import CursorStore
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

PROJECT = "projects/2026.10.20-daily-tasks-mcp-server"
MILESTONE = f"{PROJECT}/m2-planning-session-spike"
BLOCKER_ID = "019a4b2c-1f00-7a10-8000-000000000005"
ARGV = ["--user-email", "jordan@example.com", "--timezone", "UTC"]
NOW = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)


def _call(request_id: int, name: str, **arguments: JsonValue) -> dict[str, JsonValue]:
    return {
        "jsonrpc": "2.0",
        "id": request_id,
        "method": "tools/call",
        "params": {"name": name, "arguments": arguments},
    }


def _serve(root: Path, *calls: dict[str, JsonValue], extra: tuple[str, ...] = ()) -> list[dict[str, JsonValue]]:
    stdin = io.StringIO("\n".join(json.dumps(c) for c in calls) + "\n")
    stdout = io.StringIO()
    assert cli(["--workspace-root", str(root), *ARGV, *extra], environ={}, stdin=stdin, stdout=stdout) == 0
    bodies: list[dict[str, JsonValue]] = []
    for line in stdout.getvalue().splitlines():
        result = json.loads(line)["result"]
        bodies.append(result["structuredContent"])
    return bodies


def _windows(body: dict[str, JsonValue]) -> dict[str, dict[str, JsonValue]]:
    payload = body["payload"]
    assert isinstance(payload, dict) and isinstance(payload["fetch_windows"], list)
    return {str(w["source"]): w for w in payload["fetch_windows"] if isinstance(w, dict)}


def _since(window: dict[str, JsonValue]) -> datetime:
    return datetime.fromisoformat(str(window["since"]))


def _vault(root: Path) -> None:
    for relative, sample in (
        (f"{PROJECT}/project-index.md", "5-sample-project-index.md"),
        (f"{MILESTONE}/m2-planning-session-spike.md", "6-sample-milestone.md"),
        (f"{MILESTONE}/t1-wire-gmail-connector.md", "4-sample-task.md"),
        (f"{PROJECT}/blockers/b1-google-oauth-app-verification.md", "7-sample-blocker.md"),
    ):
        (root / relative).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(SPECS_ROOT / sample, root / relative)
    (root / "daily-plans").mkdir()


def _harness_message(external_id: str, received_at: datetime) -> dict[str, JsonValue]:
    return {
        "id": f"gmail:{external_id}",
        "source": "gmail",
        "external_id": external_id,
        "thread_id": f"gmail-thread:{external_id}",
        "received_at": received_at.isoformat().replace("+00:00", "Z"),
        "from": {"name": "Sarah", "address": "sarah@example.com"},
        "to": [{"name": "Jordan", "address": "jordan@example.com"}],
        "cc": [],
        "channel": None,
        "subject": "Google OAuth app verification",
        "snippet": "Google approved the OAuth app.",
        "body": f"Google OAuth app verification is resolved. ref {BLOCKER_ID}",
        "body_format": "text",
        "attachments": [],
        "url": None,
        "fetched_at": NOW.isoformat().replace("+00:00", "Z"),
    }


def test_get_fetch_window_first_pull_defaults_to_7_days(tmp_path: Path) -> None:
    before = datetime.now(UTC)

    body = _serve(tmp_path, _call(1, "daily_tasks_get_fetch_window"))[0]

    windows = _windows(body)
    assert body["status"] == "ok" and sorted(windows) == ["gmail", "slack"]
    gmail = windows["gmail"]
    assert (gmail["has_cursor"], gmail["last_external_id"], gmail["initial_lookback_days"]) == (False, None, 7)
    assert before - timedelta(days=7, seconds=5) <= _since(gmail) <= datetime.now(UTC) - timedelta(days=7)
    assert gmail["after_epoch"] == int(_since(gmail).timestamp())


@pytest.mark.parametrize(
    ("profile", "extra", "days"),
    [
        ({"sources": {"initialLookbackDays": 3}}, (), 3),
        ({"initialLookbackDays": 2}, (), 2),
        ({"sources": {"initialLookbackDays": 3}}, ("--initial-lookback-days", "10"), 10),
    ],
)
def test_get_fetch_window_custom_lookback_bounds_first_pull(
    tmp_path: Path, profile: dict[str, JsonValue], extra: tuple[str, ...], days: int
) -> None:
    state = tmp_path / ".nyssa-ai/daily-tasks"
    state.mkdir(parents=True)
    (state / "profile.json").write_text(json.dumps(profile), encoding="utf-8")

    body = _serve(tmp_path, _call(1, "daily_tasks_get_fetch_window", sources=["slack"]), extra=extra)[0]

    slack = _windows(body)["slack"]
    assert slack["initial_lookback_days"] == days
    assert datetime.now(UTC) - _since(slack) == pytest.approx(timedelta(days=days), abs=timedelta(seconds=5))


def test_get_fetch_window_subsequent_pull_uses_saved_cursor(tmp_path: Path) -> None:
    state = tmp_path / ".nyssa-ai/daily-tasks"
    state.mkdir(parents=True)
    cursor = {"since": "2026-11-01T08:00:00Z", "last_external_id": "m9", "last_run_at": None, "last_status": "ok"}
    cursors = {"workspace_root": tmp_path.as_posix(), "cursors": {"gmail": {**cursor, "last_error": None}}}
    (state / "fetch-cursors.json").write_text(json.dumps(cursors), encoding="utf-8")

    gmail = _windows(_serve(tmp_path, _call(1, "daily_tasks_get_fetch_window", sources=["gmail"]))[0])["gmail"]

    assert (gmail["has_cursor"], gmail["since"], gmail["last_external_id"]) == (True, "2026-11-01T08:00:00Z", "m9")
    assert gmail["after_epoch"] == int(datetime(2026, 11, 1, 8, tzinfo=UTC).timestamp())


@pytest.mark.parametrize("days", ["0", "-2"])
def test_cli_non_positive_initial_lookback_exits_2(
    tmp_path: Path, days: str, capsys: pytest.CaptureFixture[str]
) -> None:
    argv = ["--workspace-root", str(tmp_path), *ARGV, "--initial-lookback-days", days]

    code = cli(argv, environ={}, stdin=io.StringIO(""), stdout=io.StringIO())

    assert code == 2 and "positive integer" in capsys.readouterr().err


def test_start_session_rejects_malformed_harness_message(tmp_path: Path) -> None:
    (tmp_path / "projects").mkdir()

    body = _serve(tmp_path, _call(1, "daily_tasks_start_session", messages=[{"id": "gmail:x"}]))[0]

    assert (body["status"], body["code"]) == ("error", "Validation")
    assert not (tmp_path / ".nyssa-ai/daily-tasks/fetch-cursors.json").exists()


def _planning_server(root: Path) -> McpServer:
    settings = ServerSettings(
        workspace_root=root,
        projects_root=root / "projects",
        daily_plans_root=root / "daily-plans",
        state_root=root / ".nyssa-ai/daily-tasks",
        user=GraphUser(name="Jordan", email="jordan@example.com"),
        timezone="UTC",
    )
    numbers = count(1)

    def new_id() -> UUID:
        return UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")

    cursors = CursorStore(settings.state_root, root.as_posix())
    store = MarkdownFileStore(root, lambda: NOW, settings.projects_root, settings.daily_plans_root, settings.state_root)
    reader = MarkdownWorkspaceReader(settings, cursor_store=cursors)
    return McpServer(PlanningTools(settings, reader, store, lambda: NOW, new_id, cursors), "test")


def _handle(server: McpServer, call: dict[str, JsonValue]) -> dict[str, JsonValue]:
    response = asyncio.run(server.handle(json.dumps(call)))
    assert response is not None
    body = json.loads(response)["result"]["structuredContent"]
    assert isinstance(body, dict)
    return body


def test_start_session_harness_messages_suggest_and_advance_cursor_on_confirm(tmp_path: Path) -> None:
    _vault(tmp_path)
    server = _planning_server(tmp_path)
    fresh = _harness_message("h2", NOW - timedelta(hours=1))
    stale = _harness_message("h1", NOW - timedelta(days=8))
    cursor_file = tmp_path / ".nyssa-ai/daily-tasks/fetch-cursors.json"

    started = _handle(server, _call(1, "daily_tasks_start_session", messages=[stale, fresh], checked_sources=["gmail"]))

    payload = started["payload"]
    assert started["status"] == "ok" and isinstance(payload, dict)
    assert payload["pending_suggestions"] == 1
    assert payload["message_sources"] == [{"name": "gmail", "status": "ok", "error": None}]
    assert "gmail:h2" in str(payload["screen"]) and "gmail:h1" not in str(payload["screen"])
    assert not cursor_file.exists()

    session_id = str(started["session_id"])
    advanced = _handle(server, _call(2, "daily_tasks_advance_screen", session_id=session_id, target_screen=3))
    confirmed = _handle(server, _call(3, "daily_tasks_confirm_plan", session_id=session_id, confirmed=True))

    assert (advanced["status"], confirmed["status"]) == ("ok", "ok"), confirmed["message"]
    gmail = json.loads(cursor_file.read_text(encoding="utf-8"))["cursors"]["gmail"]
    assert (gmail["last_external_id"], gmail["since"]) == ("h2", "2026-11-03T13:30:00Z")
    after = _windows(_handle(server, _call(4, "daily_tasks_get_fetch_window", sources=["gmail"])))["gmail"]
    assert (after["has_cursor"], after["since"], after["last_external_id"]) == (True, "2026-11-03T13:30:00Z", "h2")
    again = _handle(server, _call(5, "daily_tasks_start_session", messages=[fresh]))
    assert isinstance(again["payload"], dict) and again["payload"]["pending_suggestions"] == 0
