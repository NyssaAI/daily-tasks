"""Responsibility: Verify CLI dynamic vault_root tool arguments and user_home -> repo_root profile merging.
Public interface:
+-- test_cli_boot_without_vault_root_accepts_vault_root_in_start_session(tmp_path)
+-- test_cli_layered_profile_merges_user_home_and_repo_root(tmp_path)
`-- test_cli_rejects_agent_runtime_root_as_vault_root_flag(tmp_path, capsys)

Tests for `daily-tasks-mcp` booting without `--vault-root` and merging `user_home` + `repo_root` `profile.json` files.
"""

import io
import json
from pathlib import Path

import pytest

from conftest import SAMPLES_ROOT
from daily_tasks.cli import cli


def test_cli_boot_without_vault_root_accepts_vault_root_in_start_session(tmp_path: Path) -> None:
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"
    config_dir.mkdir(parents=True)
    runtime_root = tmp_path / "runtime"
    vault = tmp_path / "vault"
    (vault / "1-projects").mkdir(parents=True)
    (vault / "2-areas" / "daily-plans").mkdir(parents=True)

    profile = {
        "schema_version": 2,
        "user": {"name": "Test User", "email": "test@example.com"},
        "timezone": "America/Chicago",
    }
    (config_dir / "profile.json").write_text(json.dumps(profile), encoding="utf-8")

    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "daily_tasks_start_session", "arguments": {"vault_root": str(vault)}},
        },
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()

    code = cli(
        ["--config-dir", str(config_dir), "--runtime-root", str(runtime_root)],
        environ={},
        stdin=stdin,
        stdout=stdout,
    )
    assert code == 0
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    assert len(responses) == 2
    tool_reply = responses[1]["result"]["structuredContent"]
    assert tool_reply["status"] == "ok"
    assert not (vault / ".nyssa-ai").exists()


def test_cli_layered_profile_merges_user_home_and_repo_root(tmp_path: Path) -> None:
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

    repo_root = tmp_path / "repo"
    repo_cfg = repo_root / ".nyssa-ai" / "daily-tasks"
    repo_cfg.mkdir(parents=True)
    vault = (tmp_path / "vault").resolve()
    (repo_cfg / "profile.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "vaults": {
                    vault.as_posix(): {
                        "projectsRoot": "my-projects",
                        "dailyPlansRelative": "my-plans",
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    proj = vault / "my-projects" / "2026.10.20-daily-tasks-mcp-server"
    ms = proj / "m2-planning-session-spike"
    ms.mkdir(parents=True)
    (proj / "project-index.md").write_bytes((SAMPLES_ROOT / "5-sample-project-index.md").read_bytes())
    (ms / "m2-planning-session-spike.md").write_bytes((SAMPLES_ROOT / "6-sample-milestone.md").read_bytes())
    (ms / "t1-wire-gmail-connector.md").write_bytes((SAMPLES_ROOT / "4-sample-task.md").read_bytes())
    (vault / "my-plans").mkdir()

    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "daily_tasks_get_fetch_window", "arguments": {"vault_root": str(vault)}},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "daily_tasks_start_session",
                "arguments": {"vault_root": str(vault)},
            },
        },
    ]
    stdin = io.StringIO("\n".join(json.dumps(line) for line in lines) + "\n")
    stdout = io.StringIO()

    code = cli(
        [
            "--config-dir",
            str(config_dir),
            "--repo-root",
            str(repo_root),
            "--runtime-root",
            str(tmp_path / "runtime"),
        ],
        environ={},
        stdin=stdin,
        stdout=stdout,
    )
    assert code == 0
    responses = [json.loads(line) for line in stdout.getvalue().splitlines()]
    window_reply = responses[1]["result"]["structuredContent"]
    assert window_reply["status"] == "ok"
    assert window_reply["payload"]["initial_lookback_days"] == 14

    start_reply = responses[2]["result"]["structuredContent"]
    assert start_reply["status"] == "ok"
    assert "America/New_York" in start_reply["payload"]["screen"]
    assert "Wire Gmail connector" in start_reply["payload"]["screen"] or "1" in start_reply["payload"]["screen"]
    assert not (vault / ".nyssa-ai").exists()


def test_cli_rejects_agent_runtime_root_as_vault_root_flag(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    agent_rt = tmp_path / "agent-work" / "hermes" / "nyssa"
    agent_rt.mkdir(parents=True)
    (agent_rt / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (agent_rt / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")

    code = cli(["--vault-root", str(agent_rt)], environ={}, stdin=io.StringIO(""), stdout=io.StringIO())
    assert code == 2
    assert "agent runtime root" in capsys.readouterr().err
