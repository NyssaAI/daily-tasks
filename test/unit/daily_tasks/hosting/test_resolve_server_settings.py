"""Responsibility: Verify ProfileStore user_home -> repo_root layering, 5-root defaults, and vault_root guards.
Public interface:
+-- test_profile_store_fails_closed_on_corrupt_or_non_object_json(tmp_path, raw_content)
+-- test_profile_store_ignores_any_files_inside_vault_root(tmp_path)
+-- test_profile_store_merges_user_home_and_repo_root_and_per_vault_map(tmp_path)
+-- test_profile_store_missing_files_returns_empty_dict(tmp_path)
+-- test_profile_store_reads_legacy_profile_json_as_readonly_fallback_and_config_json_wins(tmp_path)
+-- test_profile_store_rejects_non_v2_schema_version(tmp_path, bad_version)
+-- test_resolve_server_settings_defaults_to_1_projects_and_2_areas_daily_plans(tmp_path)
+-- test_resolve_server_settings_permits_explicit_absolute_external_projects_root(tmp_path)
+-- test_resolve_server_settings_rejects_absolute_daily_plans_outside_vault(tmp_path)
+-- test_resolve_server_settings_rejects_agent_runtime_root_as_vault_root(tmp_path)
+-- test_resolve_server_settings_rejects_daily_plans_escaping_vault_or_inside_nyssa_ai(tmp_path, plans_path)
+-- test_resolve_server_settings_rejects_missing_or_relative_vault_root(tmp_path)
+-- test_resolve_server_settings_rejects_relative_projects_root_traversal(tmp_path)
+-- test_resolve_server_settings_rejects_vault_root_colliding_with_runtime_root(tmp_path)
+-- test_resolve_server_settings_validates_identity_timezone_and_lookback(tmp_path, email, tz, lookback)
`-- test_usage_telemetry_opt_in_default_false_writes_zero_files_and_true_appends_jsonl(tmp_path)

Unit tests for `ProfileStore` and `resolve_server_settings`.
"""

from __future__ import annotations

import asyncio
import json
from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID

import pytest
from nyssa_ai_result import Err, Ok

from daily_tasks.hosting import (
    LEGACY_PROFILE_FILENAME,
    USAGE_EVENTS_RELATIVE_PATH,
    USER_CONFIG_FILENAME,
    ProfileStore,
    ServerOverrides,
    compose_mcp_server,
    record_usage_event,
    resolve_default_vault_root,
    resolve_server_settings,
)


def _write_profile(directory: Path, payload: object, *, filename: str = USER_CONFIG_FILENAME) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (directory / filename).write_text(text, encoding="utf-8")


def test_profile_store_missing_files_returns_empty_dict(tmp_path: Path) -> None:
    store = ProfileStore(config_dir=tmp_path / "config", repo_root=tmp_path / "repo")
    result = store.read_layered(tmp_path / "vault")

    assert isinstance(result, Ok)
    assert result.value == {}


def test_profile_store_merges_user_home_and_repo_root_and_per_vault_map(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    repo_root = tmp_path / "repo"
    vault = (tmp_path / "vault").resolve()
    vault.mkdir()
    _write_profile(
        config_dir,
        {
            "schema_version": 2,
            "user": {"name": "Global Jordan", "email": "jordan@example.com"},
            "sources": {"initialLookbackDays": 10, "gmail": {"enabled": True}},
            "templates": {"dailyPlan": "global-plan.md"},
            "timezone": "America/Chicago",
            "vaults": {
                vault.as_posix(): {
                    "projectsRoot": "vault-projects",
                    "dailyPlansRelative": "vault-plans",
                }
            },
        },
    )
    _write_profile(
        repo_root / ".nyssa-ai" / "daily-tasks",
        {
            "schema_version": 2,
            "user": {"name": "Repo Jordan"},
            "sources": {"initialLookbackDays": 3},
        },
    )

    result = ProfileStore(config_dir=config_dir, repo_root=repo_root).read_layered(vault)

    assert isinstance(result, Ok)
    assert result.value["user"] == {"name": "Repo Jordan", "email": "jordan@example.com"}
    assert result.value["sources"] == {"initialLookbackDays": 3, "gmail": {"enabled": True}}
    assert result.value["templates"] == {"dailyPlan": "global-plan.md"}
    assert result.value["projectsRoot"] == "vault-projects"
    assert result.value["dailyPlansRelative"] == "vault-plans"


def test_profile_store_ignores_any_files_inside_vault_root(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    vault = tmp_path / "vault"
    vault.mkdir()
    # Even if an old/stray file exists inside vault/.nyssa-ai, ProfileStore must never read it!
    _write_profile(vault / ".nyssa-ai" / "daily-tasks", "{corrupt-json-that-would-fail-if-read")
    _write_profile(
        config_dir,
        {"schema_version": 2, "user": {"email": "jordan@example.com"}, "timezone": "America/Chicago"},
    )

    result = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Ok)
    assert result.value.projects_root == (vault / "1-projects").resolve()
    assert result.value.daily_plans_root == (vault / "2-areas/daily-plans").resolve()


@pytest.mark.parametrize("raw_content", ["{malformed", '["array-root"]', '"string-root"'])
def test_profile_store_fails_closed_on_corrupt_or_non_object_json(tmp_path: Path, raw_content: str) -> None:
    config_dir = tmp_path / "config"
    _write_profile(config_dir, raw_content)

    result = ProfileStore(config_dir=config_dir).read_layered(tmp_path / "vault")

    assert isinstance(result, Err)
    assert result.category == "Validation"


@pytest.mark.parametrize("bad_version", [None, 1, 3, True, "2"])
def test_profile_store_rejects_non_v2_schema_version(tmp_path: Path, bad_version: object) -> None:
    config_dir = tmp_path / "config"
    payload: dict[str, object] = {"user": {"email": "jordan@example.com"}, "timezone": "UTC"}
    if bad_version is not None:
        payload["schema_version"] = bad_version
    _write_profile(config_dir, payload)

    result = ProfileStore(config_dir=config_dir).read_layered(tmp_path / "vault")

    assert isinstance(result, Err)
    assert result.category == "Validation"
    assert '"schema_version": 2' in result.message


def test_resolve_server_settings_defaults_to_1_projects_and_2_areas_daily_plans(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    non_para_vault = tmp_path / "plain-vault"
    non_para_vault.mkdir()
    _write_profile(
        config_dir,
        {"schema_version": 2, "user": {"email": "jordan@example.com"}, "timezone": "America/Chicago"},
    )

    result = resolve_server_settings(
        non_para_vault,
        ServerOverrides(config_dir=config_dir),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Ok)
    settings = result.value
    assert settings.vault_root == non_para_vault.resolve()
    assert settings.projects_root == (non_para_vault / "1-projects").resolve()
    assert settings.daily_plans_root == (non_para_vault / "2-areas/daily-plans").resolve()
    assert settings.runtime_root == (config_dir / "runtime").resolve()
    assert settings.user.email == "jordan@example.com"
    assert settings.user.name == "jordan@example.com"
    assert settings.timezone == "America/Chicago"
    assert settings.initial_lookback_days == 7


def test_resolve_server_settings_rejects_agent_runtime_root_as_vault_root(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    agent_runtime = tmp_path / "agent-work" / "hermes" / "nyssa"
    agent_runtime.mkdir(parents=True)
    (agent_runtime / "SOUL.md").write_text("# Soul\n", encoding="utf-8")
    (agent_runtime / "IDENTITY.md").write_text("# Identity\n", encoding="utf-8")
    _write_profile(
        config_dir,
        {
            "schema_version": 2,
            "user": {"email": "jordan@example.com"},
            "timezone": "UTC",
            "defaultVaultRoot": str(agent_runtime),
        },
    )

    direct = resolve_server_settings(agent_runtime, ServerOverrides(config_dir=config_dir), environ={}, cwd=tmp_path)
    assert isinstance(direct, Err)
    assert "agent runtime root" in direct.message

    via_default = resolve_default_vault_root(config_dir=config_dir)
    assert isinstance(via_default, Err)
    assert "agent runtime root" in via_default.message


def test_resolve_server_settings_rejects_missing_or_relative_vault_root(tmp_path: Path) -> None:
    missing = resolve_server_settings(None, ServerOverrides(config_dir=tmp_path / "empty"), environ={}, cwd=tmp_path)
    relative = resolve_server_settings(
        Path("relative/vault"),
        ServerOverrides(config_dir=tmp_path / "empty"),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(missing, Err) and "Vault root is required" in missing.message
    assert isinstance(relative, Err) and "--vault-root must be an absolute path." in relative.message


def test_resolve_server_settings_rejects_relative_projects_root_traversal(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    result = resolve_server_settings(
        vault,
        ServerOverrides(
            projects_root="../outside-projects",
            user_email="jordan@example.com",
            timezone="UTC",
            config_dir=tmp_path / "config",
        ),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Err)
    assert "projectsRoot" in result.message


def test_resolve_server_settings_permits_explicit_absolute_external_projects_root(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    external_projects = tmp_path / "external-projects"
    vault.mkdir()
    external_projects.mkdir()

    result = resolve_server_settings(
        vault,
        ServerOverrides(
            projects_root=str(external_projects),
            user_email="jordan@example.com",
            timezone="UTC",
            config_dir=tmp_path / "config",
        ),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Ok)
    assert result.value.projects_root == external_projects.resolve()


@pytest.mark.parametrize(
    "plans_path",
    [
        "../outside-plans",
        ".nyssa-ai/daily-tasks/plans",
    ],
)
def test_resolve_server_settings_rejects_daily_plans_escaping_vault_or_inside_nyssa_ai(
    tmp_path: Path,
    plans_path: str,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    result = resolve_server_settings(
        vault,
        ServerOverrides(
            daily_plans_root=plans_path,
            user_email="jordan@example.com",
            timezone="UTC",
            config_dir=tmp_path / "config",
        ),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Err)
    assert "dailyPlansRelative must stay within vaultRoot" in result.message


def test_resolve_server_settings_rejects_absolute_daily_plans_outside_vault(tmp_path: Path) -> None:
    vault = tmp_path / "vault"
    outside = tmp_path / "outside"
    vault.mkdir()
    outside.mkdir()

    result = resolve_server_settings(
        vault,
        ServerOverrides(
            user_email="jordan@example.com",
            timezone="UTC",
            daily_plans_root=str(outside),
            config_dir=tmp_path / "config",
        ),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Err)
    assert "dailyPlansRelative must stay within vaultRoot" in result.message


@pytest.mark.parametrize(
    ("email", "tz", "lookback"),
    [
        (None, "UTC", 7),
        ("jordan@example.com", None, 7),
        ("jordan@example.com", "system", 7),
        ("jordan@example.com", "UTC", 0),
        ("jordan@example.com", "UTC", -3),
    ],
)
def test_resolve_server_settings_validates_identity_timezone_and_lookback(
    tmp_path: Path,
    email: str | None,
    tz: str | None,
    lookback: int,
) -> None:
    vault = tmp_path / "vault"
    vault.mkdir()

    result = resolve_server_settings(
        vault,
        ServerOverrides(
            user_email=email,
            timezone=tz,
            initial_lookback_days=lookback,
            config_dir=tmp_path / "config",
        ),
        environ={},
        cwd=tmp_path,
    )

    assert isinstance(result, Err)
    assert result.category == "Validation"


def test_profile_store_reads_legacy_profile_json_as_readonly_fallback_and_config_json_wins(tmp_path: Path) -> None:
    config_dir = tmp_path / "home" / ".nyssa-ai" / "daily-tasks"
    repo_root = tmp_path / "repo"
    repo_dir = repo_root / ".nyssa-ai" / "daily-tasks"
    vault = (tmp_path / "vault").resolve()
    vault.mkdir()

    # Legacy profile.json in both user_dir and repo_dir when config.json is absent
    legacy_user = {
        "schema_version": 2,
        "user": {"name": "Legacy User", "email": "legacy@example.com"},
        "timezone": "America/Chicago",
    }
    legacy_repo = {
        "schema_version": 2,
        "sources": {"initialLookbackDays": 5},
    }
    _write_profile(config_dir, legacy_user, filename=LEGACY_PROFILE_FILENAME)
    _write_profile(repo_dir, legacy_repo, filename=LEGACY_PROFILE_FILENAME)

    store = ProfileStore(config_dir=config_dir, repo_root=repo_root)
    assert store.user_config_path == config_dir / USER_CONFIG_FILENAME
    assert store.repo_config_path == repo_dir / USER_CONFIG_FILENAME
    assert store.user_profile_path == config_dir / LEGACY_PROFILE_FILENAME
    assert store.repo_profile_path == repo_dir / LEGACY_PROFILE_FILENAME

    fallback_res = store.read_layered(vault)
    assert isinstance(fallback_res, Ok)
    assert fallback_res.value["user"] == {"name": "Legacy User", "email": "legacy@example.com"}
    assert fallback_res.value["sources"] == {"initialLookbackDays": 5}

    # Writing via write_user_profile ALWAYS writes config.json and leaves legacy profile.json untouched
    legacy_before = (config_dir / LEGACY_PROFILE_FILENAME).read_text(encoding="utf-8")
    canonical_user = {
        "schema_version": 2,
        "user": {"name": "Canonical User", "email": "canonical@example.com"},
        "timezone": "America/New_York",
    }
    write_res = store.write_user_profile(canonical_user)
    assert isinstance(write_res, Ok)
    assert (config_dir / USER_CONFIG_FILENAME).is_file()
    assert (config_dir / LEGACY_PROFILE_FILENAME).read_text(encoding="utf-8") == legacy_before
    assert store.user_profile_path == config_dir / USER_CONFIG_FILENAME

    # Canonical config.json in user_dir and repo_dir takes precedence over legacy profile.json
    _write_profile(
        repo_dir,
        {"schema_version": 2, "sources": {"initialLookbackDays": 12}},
        filename=USER_CONFIG_FILENAME,
    )
    assert store.repo_profile_path == repo_dir / USER_CONFIG_FILENAME

    precedence_res = store.read_layered(vault)
    assert isinstance(precedence_res, Ok)
    assert precedence_res.value["user"] == {"name": "Canonical User", "email": "canonical@example.com"}
    assert precedence_res.value["timezone"] == "America/New_York"
    assert precedence_res.value["sources"] == {"initialLookbackDays": 12}


def test_resolve_server_settings_rejects_vault_root_colliding_with_runtime_root(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_profile(
        config_dir,
        {"schema_version": 2, "user": {"email": "jordan@example.com"}, "timezone": "UTC"},
    )

    exact_collision = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir, runtime_root=vault),
        environ={},
        cwd=tmp_path,
    )
    assert isinstance(exact_collision, Err)
    assert "must not collide" in exact_collision.message

    nested_collision = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir, runtime_root=vault / "runtime"),
        environ={},
        cwd=tmp_path,
    )
    assert isinstance(nested_collision, Err)
    assert "must not collide" in nested_collision.message


def test_usage_telemetry_opt_in_default_false_writes_zero_files_and_true_appends_jsonl(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    runtime_root = tmp_path / "runtime"
    vault = tmp_path / "vault"
    vault.mkdir()
    _write_profile(
        config_dir,
        {"schema_version": 2, "user": {"email": "jordan@example.com"}, "timezone": "UTC"},
    )

    # Default telemetry_enabled is False and creates zero usage/ directories or files
    default_settings = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        environ={},
        cwd=tmp_path,
    )
    assert isinstance(default_settings, Ok)
    assert default_settings.value.telemetry_enabled is False

    disabled_event = record_usage_event(runtime_root, {"event": "noop"}, enabled=False)
    assert isinstance(disabled_event, Ok) and disabled_event.value is None
    assert not (runtime_root / "usage").exists()

    def clock() -> datetime:
        return datetime(2026, 11, 13, 14, 0, tzinfo=UTC)

    def new_id() -> UUID:
        return UUID("019a4b2c-9000-7000-8000-000000000001")
    server_disabled = compose_mcp_server(
        ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        version="0.11.2",
        clock=clock,
        new_id=new_id,
        environ={},
        cwd=tmp_path,
    )
    call_line = json.dumps(
        {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/call",
            "params": {"name": "daily_tasks_setup_status", "arguments": {"vault_root": str(vault)}},
        }
    )
    assert asyncio.run(server_disabled.handle(call_line)) is not None
    assert not (runtime_root / "usage").exists()

    # Invalid telemetry shape is rejected by strict v2 config validation
    _write_profile(
        config_dir,
        {
            "schema_version": 2,
            "user": {"email": "jordan@example.com"},
            "timezone": "UTC",
            "telemetry": {"enabled": "yes"},
        },
    )
    bad_telemetry = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        environ={},
        cwd=tmp_path,
    )
    assert isinstance(bad_telemetry, Err) and "telemetry.enabled" in bad_telemetry.message

    # Opt-in telemetry.enabled = True resolves True and appends JSONL to <runtime_root>/usage/events.jsonl
    _write_profile(
        config_dir,
        {
            "schema_version": 2,
            "user": {"email": "jordan@example.com"},
            "timezone": "UTC",
            "telemetry": {"enabled": True},
        },
    )
    enabled_settings = resolve_server_settings(
        vault,
        ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        environ={},
        cwd=tmp_path,
    )
    assert isinstance(enabled_settings, Ok)
    assert enabled_settings.value.telemetry_enabled is True

    server_enabled = compose_mcp_server(
        ServerOverrides(config_dir=config_dir, runtime_root=runtime_root),
        version="0.11.2",
        clock=clock,
        new_id=new_id,
        environ={},
        cwd=tmp_path,
    )
    assert asyncio.run(server_enabled.handle(call_line)) is not None
    events_file = runtime_root / USAGE_EVENTS_RELATIVE_PATH
    assert events_file.is_file()
    lines = [json.loads(line) for line in events_file.read_text(encoding="utf-8").splitlines()]
    assert len(lines) == 1
    assert lines[0]["event"] == "mcp.tool_call"
    assert lines[0]["tool"] == "daily_tasks_setup_status"
    assert lines[0]["status"] == "ok"
