"""Responsibility: Resolve ServerSettings dynamically across user and workspace profile layers.
Public interface:
+-- is_agent_persona_workspace(workspace_root)
+-- read_layered_profile(workspace_root, config_dir)
+-- resolve_default_workspace_root(config_dir)
`-- resolve_server_settings(workspace_root, overrides)

Resolve validated `ServerSettings` from user and workspace Schema Version 2 `profile.json` layers,
failing closed whenever workspace setup is incomplete or legacy v1 configuration has not been migrated.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.domain import GraphUser
from daily_tasks.server.types import ServerOverrides, ServerSettings

_STATE_DIR_NAME: Final = Path(".nyssa-ai") / "daily-tasks"
_LEGACY_STATE_DIR_NAME: Final = Path(".nyssaai") / "daily-tasks"
_REQUIRED_SCHEMA_VERSION: Final = 2
_DEFAULT_LOOKBACK_DAYS: Final = 7
_DEFAULT_OVERRIDES: Final = ServerOverrides()


def _is_schema_v2(value: JsonValue) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == _REQUIRED_SCHEMA_VERSION


def _read_profile_json(path: Path, legacy_path: Path | None = None) -> Result[dict[str, JsonValue] | None]:
    if path.is_symlink():
        return fail(f"profile.json at {path.as_posix()} must not be a symlink.", ErrorCategory.VALIDATION)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        if legacy_path is not None and legacy_path.exists():
            return fail(
                f"Setup incomplete: legacy v1 configuration found at {legacy_path.as_posix()}; "
                f"run the Daily Tasks Setup workflow to migrate to Schema Version 2 at {path.as_posix()}.",
                ErrorCategory.VALIDATION,
            )
        return ok(None)
    except OSError as exc:
        return fail(f"Unable to read profile.json at {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    try:
        loaded = json.loads(raw_text)
    except ValueError as exc:
        return fail(f"Malformed JSON in profile.json at {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    if not isinstance(loaded, dict):
        return fail(f"profile.json at {path.as_posix()} must contain a JSON object.", ErrorCategory.VALIDATION)
    if not _is_schema_v2(loaded.get("schema_version")):
        return fail(
            f'Setup incomplete: profile.json at {path.as_posix()} must declare "schema_version": 2 (run Setup).',
            ErrorCategory.VALIDATION,
        )
    return ok(loaded)


def read_layered_profile(
    workspace_root: Path | None,
    config_dir: Path | None = None,
) -> Result[dict[str, JsonValue]]:
    """Read user-level v2 `profile.json` and merge workspace-level v2 overrides when `workspace_root` is given."""
    if config_dir is not None:
        user_dir = config_dir.expanduser().resolve()
        legacy_user: Path | None = None
    else:
        home = Path.home()
        user_dir = home / _STATE_DIR_NAME
        legacy_user = home / _LEGACY_STATE_DIR_NAME / "profile.json"

    user_result = _read_profile_json(user_dir / "profile.json", legacy_path=legacy_user)
    if not user_result.ok:
        return fail(user_result.message, user_result.category)
    user_profile = user_result.value or {}

    if workspace_root is None:
        return ok(dict(user_profile))

    ws_result = _read_profile_json(
        workspace_root / _STATE_DIR_NAME / "profile.json",
        legacy_path=workspace_root / _LEGACY_STATE_DIR_NAME / "profile.json",
    )
    if not ws_result.ok:
        return fail(ws_result.message, ws_result.category)
    ws_profile = ws_result.value or {}

    merged: dict[str, JsonValue] = dict(user_profile)
    for key, value in ws_profile.items():
        existing = merged.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            merged[key] = {**existing, **value}
        else:
            merged[key] = value
    return ok(merged)


def _extract_text(data: dict[str, JsonValue], *keys: str) -> str | None:
    current: JsonValue = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current if isinstance(current, str) and current.strip() else None


def _resolve_projects_root(workspace: Path, raw_value: str) -> Result[Path]:
    raw_path = Path(raw_value).expanduser()
    if raw_path.is_absolute():
        return ok(raw_path.resolve())
    if ".." in raw_path.parts:
        return fail("projectsRoot relative path must not contain '..' traversal.", ErrorCategory.VALIDATION)
    resolved = (workspace / raw_path).resolve()
    if not resolved.is_relative_to(workspace):
        return fail("Relative projectsRoot must stay within workspaceRoot.", ErrorCategory.VALIDATION)
    return ok(resolved)


def _resolve_daily_plans_root(workspace: Path, state_root: Path, raw_value: str) -> Result[Path]:
    raw_path = Path(raw_value).expanduser()
    if not raw_path.is_absolute() and ".." in raw_path.parts:
        return fail(
            "dailyPlansRelative must stay within workspaceRoot and outside .nyssa-ai/.",
            ErrorCategory.VALIDATION,
        )
    resolved = raw_path.resolve() if raw_path.is_absolute() else (workspace / raw_path).resolve()
    if not resolved.is_relative_to(workspace) or resolved.is_relative_to(state_root):
        return fail(
            "dailyPlansRelative must stay within workspaceRoot and outside .nyssa-ai/.",
            ErrorCategory.VALIDATION,
        )
    return ok(resolved)


def _resolve_lookback_days(profile: dict[str, JsonValue], explicit: int | None) -> int | None:
    if explicit is not None:
        return explicit if explicit > 0 else None
    sources = profile.get("sources")
    nested = sources.get("initialLookbackDays") if isinstance(sources, dict) else None
    value = nested if nested is not None else profile.get("initialLookbackDays", _DEFAULT_LOOKBACK_DAYS)
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def is_agent_persona_workspace(workspace_root: Path) -> bool:
    """Return True when `workspace_root` is an agent persona folder (`SOUL.md` + `IDENTITY.md`) rather than a vault."""
    return (workspace_root / "SOUL.md").is_file() and (workspace_root / "IDENTITY.md").is_file()


def resolve_default_workspace_root(config_dir: Path | None = None) -> Result[Path | None]:
    """Read `defaultWorkspaceRoot` (or `workspaceRoot`) from user-scope Schema Version 2 `profile.json`."""
    if config_dir is not None:
        user_dir = config_dir.expanduser().resolve()
        legacy_user: Path | None = None
    else:
        home = Path.home()
        user_dir = home / _STATE_DIR_NAME
        legacy_user = home / _LEGACY_STATE_DIR_NAME / "profile.json"

    user_result = _read_profile_json(user_dir / "profile.json", legacy_path=legacy_user)
    if not user_result.ok:
        return fail(user_result.message, user_result.category)
    user_profile = user_result.value or {}
    raw_ws = _extract_text(user_profile, "defaultWorkspaceRoot") or _extract_text(user_profile, "workspaceRoot")
    if raw_ws is None:
        return ok(None)
    candidate = Path(raw_ws).expanduser()
    if not candidate.is_absolute():
        return fail("defaultWorkspaceRoot in user profile.json must be an absolute path.", ErrorCategory.VALIDATION)
    return ok(candidate)


def resolve_server_settings(
    workspace_root: Path | None,
    overrides: ServerOverrides = _DEFAULT_OVERRIDES,
) -> Result[ServerSettings]:
    """Resolve layered `ServerSettings`, refusing execution unless workspace setup is complete."""
    effective_root = workspace_root if workspace_root is not None else overrides.workspace_root
    if effective_root is None:
        return fail(
            "Workspace root is required. Pass workspace_root or run with --workspace-root.",
            ErrorCategory.VALIDATION,
        )
    candidate = effective_root.expanduser()
    if not candidate.is_absolute():
        return fail("--workspace-root must be an absolute path.", ErrorCategory.VALIDATION)
    resolved_workspace = candidate.resolve()
    if is_agent_persona_workspace(resolved_workspace):
        return fail(
            f"Refusing to use agent persona workspace {resolved_workspace.as_posix()} "
            "(contains SOUL.md and IDENTITY.md) as a Daily Tasks vault; pass the user's vault workspace_root.",
            ErrorCategory.VALIDATION,
        )

    ws_profile_path = resolved_workspace / _STATE_DIR_NAME / "profile.json"
    ws_profile_result = _read_profile_json(
        ws_profile_path,
        legacy_path=resolved_workspace / _LEGACY_STATE_DIR_NAME / "profile.json",
    )
    if not ws_profile_result.ok:
        return fail(ws_profile_result.message, ws_profile_result.category)
    if ws_profile_result.value is None:
        return fail(
            f"Workspace setup is not complete: missing {ws_profile_path.as_posix()}. "
            "Run the Daily Tasks Setup workflow before running Daily Tasks.",
            ErrorCategory.VALIDATION,
        )

    profile_result = read_layered_profile(resolved_workspace, config_dir=overrides.config_dir)
    if not profile_result.ok:
        return fail(profile_result.message, profile_result.category)
    profile = profile_result.value
    ws_profile = ws_profile_result.value

    projects_raw = overrides.projects_root or _extract_text(ws_profile, "projectsRoot")
    daily_plans_raw = overrides.daily_plans_root or _extract_text(ws_profile, "dailyPlansRelative")
    if not projects_raw or not daily_plans_raw:
        return fail(
            "Workspace setup is not complete: workspace profile.json must define projectsRoot and "
            "dailyPlansRelative (run Setup).",
            ErrorCategory.VALIDATION,
        )

    email = overrides.user_email or _extract_text(profile, "user", "email")
    tz = overrides.timezone or _extract_text(profile, "timezone")
    if not email or not tz or tz == "system":
        return fail(
            "Set --user-email and --timezone (IANA), or store user.email and timezone in profile.json (run Setup).",
            ErrorCategory.VALIDATION,
        )

    name = overrides.user_name or _extract_text(profile, "user", "name") or email
    lookback = _resolve_lookback_days(profile, overrides.initial_lookback_days)
    if lookback is None:
        return fail(
            "Initial lookback days must be a positive integer (--initial-lookback-days or initialLookbackDays).",
            ErrorCategory.VALIDATION,
        )

    state_root = (resolved_workspace / _STATE_DIR_NAME).resolve()
    projects_result = _resolve_projects_root(resolved_workspace, projects_raw)
    if not projects_result.ok:
        return fail(projects_result.message, projects_result.category)
    plans_result = _resolve_daily_plans_root(resolved_workspace, state_root, daily_plans_raw)
    if not plans_result.ok:
        return fail(plans_result.message, plans_result.category)

    return ok(
        ServerSettings(
            workspace_root=resolved_workspace,
            projects_root=projects_result.value,
            daily_plans_root=plans_result.value,
            state_root=state_root,
            user=GraphUser(name=name, email=email),
            timezone=tz,
            initial_lookback_days=lookback,
        )
    )
