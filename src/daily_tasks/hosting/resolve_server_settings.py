"""Responsibility: Resolve validated ServerSettings across user_home, repo_root, and CLI overrides.
Public interface:
+-- DEFAULT_DAILY_PLANS_RELATIVE
+-- DEFAULT_PROJECTS_ROOT
+-- resolve_default_vault_root(config_dir, repo_root)
`-- resolve_server_settings(vault_root, overrides, environ, cwd)
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.core.records.graph_user import GraphUser
from daily_tasks.hosting.profile_store import ProfileStore
from daily_tasks.hosting.resolve_runtime_root import is_agent_runtime_root, resolve_runtime_root
from daily_tasks.hosting.types import ServerOverrides, ServerSettings

DEFAULT_PROJECTS_ROOT: Final = "1-projects"
DEFAULT_DAILY_PLANS_RELATIVE: Final = "2-areas/daily-plans"
_DEFAULT_LOOKBACK_DAYS: Final = 7
_DEFAULT_OVERRIDES: Final = ServerOverrides()


def _extract_text(data: Mapping[str, JsonValue], *keys: str) -> str | None:
    current: JsonValue = dict(data)
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current.strip() if isinstance(current, str) and current.strip() else None


def _resolve_projects_root(vault: Path, raw_value: str) -> Result[Path]:
    raw_path = Path(raw_value).expanduser()
    if raw_path.is_absolute():
        return ok(raw_path.resolve())
    if ".." in raw_path.parts:
        return fail("projectsRoot relative path must not contain '..' traversal.", ErrorCategory.VALIDATION)
    resolved = (vault / raw_path).resolve()
    if not resolved.is_relative_to(vault) or resolved.is_relative_to(vault / ".nyssa-ai"):
        return fail(
            "Relative projectsRoot must stay within vaultRoot and outside .nyssa-ai/.", ErrorCategory.VALIDATION
        )
    return ok(resolved)


def _resolve_daily_plans_root(vault: Path, raw_value: str) -> Result[Path]:
    raw_path = Path(raw_value).expanduser()
    if not raw_path.is_absolute() and ".." in raw_path.parts:
        return fail(
            "dailyPlansRelative must stay within vaultRoot and outside .nyssa-ai/.",
            ErrorCategory.VALIDATION,
        )
    resolved = raw_path.resolve() if raw_path.is_absolute() else (vault / raw_path).resolve()
    if not resolved.is_relative_to(vault) or resolved.is_relative_to(vault / ".nyssa-ai"):
        return fail(
            "dailyPlansRelative must stay within vaultRoot and outside .nyssa-ai/.",
            ErrorCategory.VALIDATION,
        )
    return ok(resolved)


def _resolve_lookback_days(profile: Mapping[str, JsonValue], explicit: int | None) -> int | None:
    if explicit is not None:
        return explicit if explicit > 0 else None
    sources = profile.get("sources")
    nested = sources.get("initialLookbackDays") if isinstance(sources, dict) else None
    value = nested if nested is not None else profile.get("initialLookbackDays", _DEFAULT_LOOKBACK_DAYS)
    return value if isinstance(value, int) and not isinstance(value, bool) and value > 0 else None


def resolve_default_vault_root(config_dir: Path | None = None, repo_root: Path | None = None) -> Result[Path | None]:
    """Read `defaultVaultRoot` (or `vaultRoot`) across `user_home` -> `repo_root` Schema Version 2 profiles."""
    store = ProfileStore(config_dir=config_dir, repo_root=repo_root)
    layered = store.read_layered()
    if not layered.ok:
        return fail(layered.message, layered.category)
    raw_vault = _extract_text(layered.value, "defaultVaultRoot") or _extract_text(layered.value, "vaultRoot")
    if raw_vault is None:
        return ok(None)
    candidate = Path(raw_vault).expanduser()
    if not candidate.is_absolute():
        return fail("defaultVaultRoot in profile.json must be an absolute path.", ErrorCategory.VALIDATION)
    resolved = candidate.resolve()
    if is_agent_runtime_root(resolved):
        return fail(
            f"Refusing to use agent runtime root {resolved.as_posix()} "
            "(contains SOUL.md and IDENTITY.md) as vault_root.",
            ErrorCategory.VALIDATION,
        )
    return ok(resolved)


def resolve_server_settings(
    vault_root: Path | None,
    overrides: ServerOverrides = _DEFAULT_OVERRIDES,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> Result[ServerSettings]:
    """Resolve `ServerSettings` for `vault_root` across `user_home` -> `repo_root` and `runtime_root`."""
    effective_vault = vault_root if vault_root is not None else overrides.vault_root
    if effective_vault is None:
        default_res = resolve_default_vault_root(config_dir=overrides.config_dir, repo_root=overrides.repo_root)
        if not default_res.ok:
            return fail(default_res.message, default_res.category)
        effective_vault = default_res.value
    if effective_vault is None:
        return fail(
            "Vault root is required. Pass vault_root, configure defaultVaultRoot in Setup, or run with --vault-root.",
            ErrorCategory.VALIDATION,
        )

    candidate = effective_vault.expanduser()
    if not candidate.is_absolute():
        return fail("--vault-root must be an absolute path.", ErrorCategory.VALIDATION)
    resolved_vault = candidate.resolve()
    if is_agent_runtime_root(resolved_vault):
        return fail(
            f"Refusing to use agent runtime root {resolved_vault.as_posix()} "
            "(contains SOUL.md and IDENTITY.md) as vault_root; pass the user's vault directory.",
            ErrorCategory.VALIDATION,
        )

    store = ProfileStore(config_dir=overrides.config_dir, repo_root=overrides.repo_root)
    profile_result = store.read_layered(resolved_vault)
    if not profile_result.ok:
        return fail(profile_result.message, profile_result.category)
    profile = profile_result.value

    email = overrides.user_email or _extract_text(profile, "user", "email")
    tz = overrides.timezone or _extract_text(profile, "timezone")
    if not email or not tz or tz == "system":
        return fail(
            "Daily Tasks setup is incomplete: set --user-email and --timezone (IANA), "
            "or configure user.email and timezone in ~/.nyssa-ai/daily-tasks/profile.json (run Setup).",
            ErrorCategory.VALIDATION,
        )

    name = overrides.user_name or _extract_text(profile, "user", "name") or email
    lookback = _resolve_lookback_days(profile, overrides.initial_lookback_days)
    if lookback is None:
        return fail(
            "Initial lookback days must be a positive integer (--initial-lookback-days or initialLookbackDays).",
            ErrorCategory.VALIDATION,
        )

    projects_raw = overrides.projects_root or _extract_text(profile, "projectsRoot") or DEFAULT_PROJECTS_ROOT
    daily_plans_raw = (
        overrides.daily_plans_root or _extract_text(profile, "dailyPlansRelative") or DEFAULT_DAILY_PLANS_RELATIVE
    )

    projects_result = _resolve_projects_root(resolved_vault, projects_raw)
    if not projects_result.ok:
        return fail(projects_result.message, projects_result.category)
    plans_result = _resolve_daily_plans_root(resolved_vault, daily_plans_raw)
    if not plans_result.ok:
        return fail(plans_result.message, plans_result.category)

    runtime_result = resolve_runtime_root(
        explicit=overrides.runtime_root,
        environ=environ,
        cwd=cwd,
        configured=_extract_text(profile, "runtimeRoot"),
        config_dir=store.user_dir,
    )
    if not runtime_result.ok:
        return fail(runtime_result.message, runtime_result.category)

    return ok(
        ServerSettings(
            vault_root=resolved_vault,
            projects_root=projects_result.value,
            daily_plans_root=plans_result.value,
            runtime_root=runtime_result.value,
            user=GraphUser(name=name, email=email),
            timezone=tz,
            initial_lookback_days=lookback,
            config_dir=store.user_dir,
        )
    )
