"""Responsibility: Verify layered profile loading, fail-closed JSON validation, and workspace containment rules.
Public interface:
+-- test_read_layered_profile_fails_closed_on_corrupt_or_non_object_json(tmp_path, raw_content)
+-- test_read_layered_profile_merges_nested_dictionaries_without_losing_siblings(tmp_path)
+-- test_read_layered_profile_missing_files_returns_empty_dict(tmp_path)
+-- test_resolve_server_settings_rejects_absolute_daily_plans_outside_workspace(tmp_path)
+-- test_resolve_server_settings_rejects_daily_plans_escaping_workspace_or_inside_state(tmp_path, plans_path)
+-- test_resolve_server_settings_rejects_missing_or_relative_workspace_before_resolving()
+-- test_resolve_server_settings_succeeds_with_layered_config_dir_and_defaults_name_to_email(tmp_path)
`-- test_resolve_server_settings_validates_identity_timezone_and_lookback(tmp_path, email, tz, lookback)

Unit tests for `read_layered_profile` and `resolve_server_settings`.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok

from daily_tasks.server.resolve_server_settings import read_layered_profile, resolve_server_settings
from daily_tasks.server.types import ServerOverrides


def _write_profile(directory: Path, payload: object) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    text = payload if isinstance(payload, str) else json.dumps(payload)
    (directory / "profile.json").write_text(text, encoding="utf-8")


def test_read_layered_profile_missing_files_returns_empty_dict(tmp_path: Path) -> None:
    result = read_layered_profile(tmp_path / "workspace", config_dir=tmp_path / "config")

    assert isinstance(result, Ok)
    assert result.value == {}


def test_read_layered_profile_merges_nested_dictionaries_without_losing_siblings(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    workspace = tmp_path / "workspace"
    _write_profile(
        config_dir,
        {
            "user": {"name": "Global Jordan", "email": "jordan@example.com"},
            "sources": {"initialLookbackDays": 10, "gmail": {"enabled": True}},
            "templates": {"dailyPlan": "global-plan.md"},
            "timezone": "America/Chicago",
        },
    )
    _write_profile(
        workspace / ".nyssa-ai" / "daily-tasks",
        {
            "user": {"name": "Workspace Jordan"},
            "sources": {"initialLookbackDays": 3},
            "projectsRoot": "my-projects",
        },
    )

    result = read_layered_profile(workspace, config_dir=config_dir)

    assert isinstance(result, Ok)
    assert result.value["user"] == {"name": "Workspace Jordan", "email": "jordan@example.com"}
    assert result.value["sources"] == {"initialLookbackDays": 3, "gmail": {"enabled": True}}
    assert result.value["templates"] == {"dailyPlan": "global-plan.md"}
    assert result.value["projectsRoot"] == "my-projects"


@pytest.mark.parametrize("raw_content", ["{malformed", '["array-root"]', '"string-root"'])
def test_read_layered_profile_fails_closed_on_corrupt_or_non_object_json(tmp_path: Path, raw_content: str) -> None:
    config_dir = tmp_path / "config"
    _write_profile(config_dir, raw_content)

    result = read_layered_profile(tmp_path / "workspace", config_dir=config_dir)

    assert isinstance(result, Err)
    assert result.category == "Validation"


def test_resolve_server_settings_rejects_missing_or_relative_workspace_before_resolving() -> None:
    missing = resolve_server_settings(None)
    relative = resolve_server_settings(Path("relative/workspace"))

    assert isinstance(missing, Err) and "Workspace root is required" in missing.message
    assert isinstance(relative, Err) and "--workspace-root must be an absolute path." in relative.message


@pytest.mark.parametrize(
    "plans_path",
    [
        "../outside-plans",
        ".nyssa-ai/daily-tasks/plans",
    ],
)
def test_resolve_server_settings_rejects_daily_plans_escaping_workspace_or_inside_state(
    tmp_path: Path,
    plans_path: str,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = resolve_server_settings(
        workspace,
        ServerOverrides(
            user_email="jordan@example.com",
            timezone="UTC",
            daily_plans_root=plans_path,
            config_dir=tmp_path / "config",
        ),
    )

    assert isinstance(result, Err)
    assert "dailyPlansRelative must stay within workspaceRoot" in result.message


def test_resolve_server_settings_rejects_absolute_daily_plans_outside_workspace(tmp_path: Path) -> None:
    workspace = tmp_path / "workspace"
    outside = tmp_path / "outside"
    workspace.mkdir()
    outside.mkdir()

    result = resolve_server_settings(
        workspace,
        ServerOverrides(
            user_email="jordan@example.com",
            timezone="UTC",
            daily_plans_root=str(outside),
            config_dir=tmp_path / "config",
        ),
    )

    assert isinstance(result, Err)
    assert "dailyPlansRelative must stay within workspaceRoot" in result.message


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
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    result = resolve_server_settings(
        workspace,
        ServerOverrides(
            user_email=email,
            timezone=tz,
            initial_lookback_days=lookback,
            config_dir=tmp_path / "config",
        ),
    )

    assert isinstance(result, Err)
    assert result.category == "Validation"


def test_resolve_server_settings_succeeds_with_layered_config_dir_and_defaults_name_to_email(tmp_path: Path) -> None:
    config_dir = tmp_path / "config"
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    _write_profile(config_dir, {"user": {"email": "jordan@example.com"}, "timezone": "America/Chicago"})

    result = resolve_server_settings(workspace, ServerOverrides(config_dir=config_dir))

    assert isinstance(result, Ok)
    settings = result.value
    assert settings.workspace_root == workspace.resolve()
    assert settings.user.email == "jordan@example.com"
    assert settings.user.name == "jordan@example.com"
    assert settings.timezone == "America/Chicago"
    assert settings.initial_lookback_days == 7
