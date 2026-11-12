"""Responsibility: Verify ProfileStore user_home -> repo_root layering, 5-root defaults, and vault_root guards.
Public interface:
+-- test_profile_store_fails_closed_on_corrupt_or_non_object_json(tmp_path, raw_content)
+-- test_profile_store_ignores_any_files_inside_vault_root(tmp_path)
+-- test_profile_store_merges_user_home_and_repo_root_and_per_vault_map(tmp_path)
+-- test_profile_store_missing_files_returns_empty_dict(tmp_path)
+-- test_profile_store_rejects_non_v2_schema_version(tmp_path, bad_version)
+-- test_resolve_server_settings_defaults_to_1_projects_and_2_areas_daily_plans(tmp_path)
+-- test_resolve_server_settings_permits_explicit_absolute_external_projects_root(tmp_path)
+-- test_resolve_server_settings_rejects_absolute_daily_plans_outside_vault(tmp_path)
+-- test_resolve_server_settings_rejects_agent_runtime_root_as_vault_root(tmp_path)
+-- test_resolve_server_settings_rejects_daily_plans_escaping_vault_or_inside_nyssa_ai(tmp_path, plans_path)
+-- test_resolve_server_settings_rejects_missing_or_relative_vault_root(tmp_path)
+-- test_resolve_server_settings_rejects_relative_projects_root_traversal(tmp_path)
`-- test_resolve_server_settings_validates_identity_timezone_and_lookback(tmp_path, email, tz, lookback)

Unit tests for `ProfileStore` and `resolve_server_settings`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok

from daily_tasks.hosting import ProfileStore, ServerOverrides, resolve_default_vault_root, resolve_server_settings


def _write_profile(directory: Path, payload: object) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (directory / "profile.json").write_text(text, encoding="utf-8")


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
