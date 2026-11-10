"""Responsibility: Resolve ServerSettings dynamically across user and workspace profile layers.
Public interface:
+-- read_layered_profile(workspace_root, config_dir)
`-- resolve_server_settings(workspace_root, overrides)

Resolve validated `ServerSettings` from user and workspace `profile.json` layers.
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
_DEFAULT_LOOKBACK_DAYS: Final = 7
_DEFAULT_OVERRIDES: Final = ServerOverrides()


def _read_profile_json(path: Path) -> Result[dict[str, JsonValue]]:
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ok({})
    except OSError as exc:
        return fail(f"Unable to read profile.json at {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    try:
        loaded = json.loads(raw_text)
    except ValueError as exc:
        return fail(f"Malformed JSON in profile.json at {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    if not isinstance(loaded, dict):
        return fail(f"profile.json at {path.as_posix()} must contain a JSON object.", ErrorCategory.VALIDATION)
    return ok(loaded)


def read_layered_profile(
    workspace_root: Path | None,
    config_dir: Path | None = None,
) -> Result[dict[str, JsonValue]]:
    """Read user-level `profile.json` and merge workspace-level overrides when `workspace_root` is given."""
    user_dir = config_dir.expanduser().resolve() if config_dir is not None else Path.home() / _STATE_DIR_NAME
    user_result = _read_profile_json(user_dir / "profile.json")
    if not user_result.ok:
        return user_result

    if workspace_root is None:
        return ok(dict(user_result.value))

    ws_result = _read_profile_json(workspace_root / _STATE_DIR_NAME / "profile.json")
    if not ws_result.ok:
        return ws_result

    merged: dict[str, JsonValue] = dict(user_result.value)
    for key, value in ws_result.value.items():
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


def _resolve_root(workspace: Path, value: str | None, default: str) -> Path:
    path = Path(value or default).expanduser()
    return path.resolve() if path.is_absolute() else (workspace / path).resolve()


def _resolve_lookback_days(profile: dict[str, JsonValue], explicit: int | None) -> int | None:
    if explicit is not None:
        return explicit if explicit > 0 else None
    sources = profile.get("sources")
    nested = sources.get("initialLookbackDays") if isinstance(sources, dict) else None
    value = nested if nested is not None else profile.get("initialLookbackDays", _DEFAULT_LOOKBACK_DAYS)
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def resolve_server_settings(
    workspace_root: Path | None,
    overrides: ServerOverrides = _DEFAULT_OVERRIDES,
) -> Result[ServerSettings]:
    """Resolve layered `ServerSettings` or return a validation failure `Result`."""
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

    profile_result = read_layered_profile(resolved_workspace, config_dir=overrides.config_dir)
    if not profile_result.ok:
        return fail(profile_result.message, profile_result.category)
    profile = profile_result.value

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
    resolved_projects = _resolve_root(
        resolved_workspace,
        overrides.projects_root or _extract_text(profile, "projectsRoot"),
        "projects",
    )
    resolved_daily_plans = _resolve_root(
        resolved_workspace,
        overrides.daily_plans_root or _extract_text(profile, "dailyPlansRelative"),
        "daily-plans",
    )
    if not resolved_daily_plans.is_relative_to(resolved_workspace) or resolved_daily_plans.is_relative_to(state_root):
        return fail(
            "dailyPlansRelative must stay within workspaceRoot and outside .nyssa-ai/.",
            ErrorCategory.VALIDATION,
        )

    return ok(
        ServerSettings(
            workspace_root=resolved_workspace,
            projects_root=resolved_projects,
            daily_plans_root=resolved_daily_plans,
            state_root=state_root,
            user=GraphUser(name=name, email=email),
            timezone=tz,
            initial_lookback_days=lookback,
        )
    )
