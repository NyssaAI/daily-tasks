"""Responsibility: Verify SetupTools zero-.nyssa-ai vault writes, defaultVaultRoot fallback, and launch_mcp.
Public interface:
+-- test_configure_vault_personal_scope_creates_no_vault_files(tmp_path)
+-- test_configure_vault_preserves_custom_templates_seeds_missing_ones_and_writes_zero_nyssa_ai_in_vault(tmp_path)
+-- test_configure_vault_rejects_unconfirmed_invalid_tz_or_agent_runtime_root(tmp_path)
+-- test_dispatcher_resolves_default_vault_root_from_user_profile_for_zero_arg_mcp(tmp_path)
+-- test_launch_mcp_runs_in_process_and_falls_back_to_uv_using_runtime_root_venv(monkeypatch, capsys)
+-- test_mcp_server_exposes_and_dispatches_setup_tools_via_cli(tmp_path)
`-- test_setup_status_detects_para_and_standard_layouts_then_passes_after_configure(tmp_path)

Unit tests for `SetupTools`, `VaultCollaboratorResolver` + `PlanningToolsDispatcher`, and `launch_mcp`.
"""

from __future__ import annotations

import builtins
import io
import json
import os
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import UUID

import pytest

from daily_tasks import launch_mcp as launch_mcp_mod
from daily_tasks.cli import cli
from daily_tasks.core.planning import PlanningToolsDispatcher
from daily_tasks.hosting import ServerOverrides, SetupTools, VaultCollaboratorResolver, resolve_server_settings
from daily_tasks.transports.mcp import VaultSetupSpec

_NOW = datetime(2026, 11, 11, 21, 0, tzinfo=UTC)


def test_setup_status_detects_para_and_standard_layouts_then_passes_after_configure(tmp_path: Path) -> None:
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"
    vault = tmp_path / "ja-vault"
    (vault / "1-projects").mkdir(parents=True)
    (vault / "2-areas" / "daily-plans").mkdir(parents=True)
    (vault / "3-resources" / "templates").mkdir(parents=True)

    tools = SetupTools(ServerOverrides(config_dir=config_dir), lambda: _NOW)
    status_before = tools.setup_status(vault_root=str(vault))

    assert status_before["status"] == "ok"
    payload_before = status_before["payload"]
    assert isinstance(payload_before, dict)
    assert payload_before["setup_complete"] is False
    assert payload_before["detected_layout"] == "para"
    proposed = payload_before["proposed_settings"]
    assert isinstance(proposed, dict)
    assert proposed["projects_root"] == "1-projects"
    assert proposed["daily_plans_relative"] == "2-areas/daily-plans"

    configured = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            vault_root=str(vault),
            user_name="Jeremy Maynor",
            user_email="jeremy@example.com",
            timezone="America/Chicago",
            priorities=["Build sustainable consulting portfolio"],
            disabled_sources=["gmail", "outlook", "slack", "teams"],
            initial_lookback_days=7,
        )
    )
    assert configured["status"] == "ok"
    assert not (vault / ".nyssa-ai").exists()

    status_after = tools.setup_status(vault_root=str(vault))
    payload_after = status_after["payload"]
    assert isinstance(payload_after, dict)
    assert payload_after["setup_complete"] is True
    assert payload_after["missing_gates"] == []


def test_configure_vault_preserves_custom_templates_seeds_missing_ones_and_writes_zero_nyssa_ai_in_vault(
    tmp_path: Path,
) -> None:
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"
    vault = tmp_path / "vault"
    tpl_dir = vault / "3-resources" / "templates"
    tpl_dir.mkdir(parents=True)
    custom_plan = tpl_dir / "daily-tasks-daily-plan.md"
    custom_plan.write_text("# My Custom Daily Plan Layout\n", encoding="utf-8")

    tools = SetupTools(ServerOverrides(config_dir=config_dir), lambda: _NOW)
    res = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            vault_root=str(vault),
            user_name="Alex",
            user_email="alex@example.com",
            timezone="America/New_York",
            disabled_sources=["gmail", "slack"],
        )
    )

    assert res["status"] == "ok"
    assert custom_plan.read_text(encoding="utf-8") == "# My Custom Daily Plan Layout\n"
    payload = res["payload"]
    assert isinstance(payload, dict)
    templates = payload["templates"]
    assert isinstance(templates, dict)
    assert templates["dailyPlan"] == "./3-resources/templates/daily-tasks-daily-plan.md"
    assert templates["projectIndex"] == "./3-resources/templates/project-index.md"
    assert (tpl_dir / "project-index.md").is_file()
    # updates.json and profile.json live strictly in config_dir, NEVER inside vault_root!
    assert (config_dir / "templates" / "updates.json").is_file()
    assert (config_dir / "profile.json").is_file()
    assert not (vault / ".nyssa-ai").exists()


def test_configure_vault_rejects_unconfirmed_invalid_tz_or_agent_runtime_root(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    vault = tmp_path / "vault"
    vault.mkdir()
    tools = SetupTools(ServerOverrides(config_dir=config_dir), lambda: _NOW)

    unconfirmed = tools.configure_vault(
        VaultSetupSpec(
            confirmed=False,
            vault_root=str(vault),
            user_name="Alex",
            user_email="alex@example.com",
            timezone="America/Chicago",
        )
    )
    assert unconfirmed["status"] == "error"
    assert unconfirmed["code"] == "Forbidden"
    assert not (config_dir / "profile.json").exists()

    system_tz = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            vault_root=str(vault),
            user_name="Alex",
            user_email="alex@example.com",
            timezone="system",
        )
    )
    assert system_tz["status"] == "error"
    assert system_tz["code"] == "Validation"

    agent_rt = tmp_path / "agent-work" / "hermes" / "nyssa"
    agent_rt.mkdir(parents=True)
    (agent_rt / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (agent_rt / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")

    rt_cfg = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            vault_root=str(agent_rt),
            user_name="Alex",
            user_email="alex@example.com",
            timezone="America/Chicago",
        )
    )
    assert rt_cfg["status"] == "error"
    assert "agent runtime root" in str(rt_cfg["message"])

    rt_settings = resolve_server_settings(agent_rt, ServerOverrides(config_dir=config_dir), environ={}, cwd=tmp_path)
    assert not rt_settings.ok
    assert "agent runtime root" in rt_settings.message


def test_configure_vault_personal_scope_creates_no_vault_files(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    untouched = tmp_path / "vault"
    tools = SetupTools(ServerOverrides(config_dir=config_dir), lambda: _NOW)

    res = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            scope="personal",
            user_name="Alex",
            user_email="alex@example.com",
            timezone="America/Chicago",
            priorities=["Focus on product strategy"],
        )
    )

    assert res["status"] == "ok"
    assert (config_dir / "profile.json").is_file()
    assert not untouched.exists()


def test_dispatcher_resolves_default_vault_root_from_user_profile_for_zero_arg_mcp(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    vault = tmp_path / "vault"
    (vault / "1-projects").mkdir(parents=True)
    tools = SetupTools(ServerOverrides(config_dir=config_dir), lambda: _NOW)
    cfg = tools.configure_vault(
        VaultSetupSpec(
            confirmed=True,
            vault_root=str(vault),
            user_name="Alex",
            user_email="alex@example.com",
            timezone="America/Chicago",
            disabled_sources=["gmail", "slack"],
            set_default_vault=True,
        )
    )
    assert cfg["status"] == "ok"

    resolver = VaultCollaboratorResolver(
        overrides=ServerOverrides(config_dir=config_dir),
        clock=lambda: _NOW,
        environ={},
        cwd=tmp_path,
    )
    dispatcher = PlanningToolsDispatcher(
        resolver=resolver,
        clock=lambda: _NOW,
        new_id=lambda: UUID("019a4b2c-9000-7000-8000-000000000001"),
    )
    fetch_reply = dispatcher.get_fetch_window()
    assert fetch_reply["status"] == "ok"


def test_mcp_server_exposes_and_dispatches_setup_tools_via_cli(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    runtime_root = tmp_path / "runtime"
    vault = tmp_path / "vault"
    vault.mkdir()
    lines = [
        {"jsonrpc": "2.0", "id": 1, "method": "tools/list"},
        {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/call",
            "params": {"name": "daily_tasks_setup_status", "arguments": {"vault_root": str(vault)}},
        },
        {
            "jsonrpc": "2.0",
            "id": 3,
            "method": "tools/call",
            "params": {
                "name": "daily_tasks_configure_vault",
                "arguments": {
                    "confirmed": True,
                    "vault_root": str(vault),
                    "user_name": "Jordan",
                    "user_email": "jordan@example.com",
                    "timezone": "America/Chicago",
                    "disabled_sources": ["gmail", "slack"],
                },
            },
        },
        {
            "jsonrpc": "2.0",
            "id": 4,
            "method": "tools/call",
            "params": {"name": "daily_tasks_get_fetch_window", "arguments": {}},
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
    tool_names = [t["name"] for t in responses[0]["result"]["tools"]]
    assert "daily_tasks_setup_status" in tool_names
    assert "daily_tasks_configure_vault" in tool_names
    assert responses[1]["result"]["structuredContent"]["payload"]["setup_complete"] is False
    assert responses[2]["result"]["structuredContent"]["payload"]["setup_complete"] is True
    assert responses[3]["result"]["structuredContent"]["status"] == "ok"
    assert not (vault / ".nyssa-ai").exists()


def test_launch_mcp_runs_in_process_and_falls_back_to_uv_using_runtime_root_venv(
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr("sys.stdin", io.StringIO(""))
    monkeypatch.setattr("sys.stdout", io.StringIO())
    assert launch_mcp_mod.launch_mcp([]) == 0

    real_import = builtins.__import__

    def fake_missing_import(name: str, *args: Any, **kwargs: Any) -> Any:
        if name == "daily_tasks.cli":
            raise ModuleNotFoundError("No module named 'pydantic'", name="pydantic")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_missing_import)

    exec_calls: list[tuple[str, list[str]]] = []

    def fake_exec(exe: str, argv: Any) -> int:
        exec_calls.append((exe, list(argv)))
        return 0

    monkeypatch.setenv("NYSSA_RUNTIME_ROOT", "/tmp/fake-nyssa-runtime")
    monkeypatch.delenv("UV_PROJECT_ENVIRONMENT", raising=False)

    assert launch_mcp_mod.launch_mcp(["--help"], which_uv=lambda _: "/usr/bin/uv", exec_uv=fake_exec) == 0
    expected_uv_args = ["/usr/bin/uv", "run", "--no-dev"]
    if (launch_mcp_mod.PLUGIN_ROOT / "uv.lock").is_file():
        expected_uv_args.append("--frozen")
    expected_uv_args.extend(["--directory", str(launch_mcp_mod.PLUGIN_ROOT), "daily-tasks-mcp", "--help"])
    assert exec_calls == [("/usr/bin/uv", expected_uv_args)]
    assert os.environ.get("UV_PROJECT_ENVIRONMENT") == str(Path("/tmp/fake-nyssa-runtime").resolve() / ".venv")

    assert launch_mcp_mod.launch_mcp([], which_uv=lambda _: None, exec_uv=fake_exec) == 2
    assert "missing Python dependency (pydantic)" in capsys.readouterr().err
