"""Responsibility: Verify CLI dynamic workspace_root tool arguments and layered user/workspace profile merging.
Public interface:
+-- test_cli_boot_without_workspace_root_accepts_workspace_root_in_start_session(tmp_path, monkeypatch)
`-- test_cli_layered_profile_merges_user_home_and_workspace_roots(tmp_path)

Tests for `daily-tasks-mcp` booting without `--workspace-root` and merging user/workspace `profile.json` files.
"""

import io
import json
from pathlib import Path

import pytest

from daily_tasks.cli import cli


def test_cli_boot_without_workspace_root_accepts_workspace_root_in_start_session(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_home = tmp_path / "fake_home"
    fake_home.mkdir()
    monkeypatch.setattr(Path, "home", lambda: fake_home)
    ws = tmp_path / "workspace"
    ws.mkdir()
    (ws / ".nyssa-ai" / "daily-tasks").mkdir(parents=True)
    profile = {
        "schema_version": 2,
        "user": {"name": "Test User", "email": "test@example.com"},
        "timezone": "America/Chicago",
        "projectsRoot": "projects",
        "dailyPlansRelative": "daily-plans",
    }
    (ws / ".nyssa-ai" / "daily-tasks" / "profile.json").write_text(json.dumps(profile), encoding="utf-8")
    (ws / "projects").mkdir()
    (ws / "daily-plans").mkdir()

    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "daily_tasks_start_session", "arguments": {"workspace_root": str(ws)}},
        },
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()

    code = cli([], environ={}, stdin=stdin, stdout=stdout)
    assert code == 0
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert len(responses) == 2
    tool_reply = responses[1]["result"]["structuredContent"]
    assert tool_reply["status"] == "ok"


def test_cli_layered_profile_merges_user_home_and_workspace_roots(tmp_path: Path) -> None:
    specs_root = Path(__file__).resolve().parents[4] / "docs" / "specs"
    config_dir = tmp_path / "user_config"
    config_dir.mkdir(parents=True)
    (config_dir / "profile.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "user": {"name": "Global User", "email": "jordan@example.com"},
                "timezone": "America/New_York",
                "sources": {"initialLookbackDays": 14},
            }
        ),
        encoding="utf-8",
    )

    ws = tmp_path / "workspace"
    ws.mkdir()
    ws_state = ws / ".nyssa-ai" / "daily-tasks"
    ws_state.mkdir(parents=True)
    (ws_state / "profile.json").write_text(
        json.dumps({"schema_version": 2, "projectsRoot": "my-projects", "dailyPlansRelative": "my-plans"}),
        encoding="utf-8",
    )
    proj = ws / "my-projects" / "2026.10.20-daily-tasks-mcp-server"
    ms = proj / "m2-planning-session-spike"
    ms.mkdir(parents=True)
    (proj / "project-index.md").write_bytes((specs_root / "5-sample-project-index.md").read_bytes())
    (ms / "m2-planning-session-spike.md").write_bytes((specs_root / "6-sample-milestone.md").read_bytes())
    (ms / "t1-wire-gmail-connector.md").write_bytes((specs_root / "4-sample-task.md").read_bytes())
    (ws / "my-plans").mkdir()

    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "daily_tasks_get_fetch_window", "arguments": {"workspace_root": str(ws)}},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "daily_tasks_start_session",
                "arguments": {"workspace_root": str(ws)},
            },
        },
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()

    code = cli(["--config-dir", str(config_dir)], environ={}, stdin=stdin, stdout=stdout)
    assert code == 0
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    window_reply = responses[1]["result"]["structuredContent"]
    assert window_reply["status"] == "ok"
    assert window_reply["payload"]["initial_lookback_days"] == 14

    start_reply = responses[2]["result"]["structuredContent"]
    assert start_reply["status"] == "ok"
    assert "America/New_York" in start_reply["payload"]["screen"]
    assert "Wire Gmail connector" in start_reply["payload"]["screen"] or "1" in start_reply["payload"]["screen"]
