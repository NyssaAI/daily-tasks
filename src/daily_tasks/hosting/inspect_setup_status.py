"""Responsibility: Inspect Schema Version 2 Daily Tasks setup gates for a vault without mutating disk.
Public interface:
+-- build_sources_config(existing_sources, spec)
`-- inspect_setup_status(store, templates, overrides, vault_root, status_tool)
"""

from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.hosting.detect_host_timezone import detect_host_timezone
from daily_tasks.hosting.profile_store import ProfileStore
from daily_tasks.hosting.resolve_runtime_root import is_agent_runtime_root
from daily_tasks.hosting.resolve_server_settings import (
    DEFAULT_DAILY_PLANS_RELATIVE,
    DEFAULT_PROJECTS_ROOT,
    resolve_server_settings,
)
from daily_tasks.hosting.types import ServerOverrides
from daily_tasks.records.template_synchronizer import TemplateSynchronizer
from daily_tasks.transports.mcp.types import VaultSetupSpec

_DEFAULT_TEMPLATES_DIR: Final = "./3-resources/templates"


def _extract_str(data: Mapping[str, JsonValue], *keys: str) -> str | None:
    current: JsonValue = dict(data)
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
        else:
            return None
    return current.strip() if isinstance(current, str) and current.strip() else None


def _extract_str_list(value: JsonValue) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item.strip() for item in value if isinstance(item, str) and item.strip()]


def _sources_valid(sources_map: JsonValue) -> bool:
    if not isinstance(sources_map, dict):
        return False
    lookback = sources_map.get("initialLookbackDays")
    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback <= 0:
        return False
    return any(
        key in sources_map
        for key in ("harnessConnections", "standaloneSources", "disabledSources", "gmail", "slack", "outlook", "teams")
    )


def build_sources_config(existing_sources: JsonValue, spec: VaultSetupSpec) -> Result[dict[str, JsonValue]]:
    """Validate and merge source settings for `config.json`."""
    base: dict[str, JsonValue] = dict(existing_sources) if isinstance(existing_sources, dict) else {}
    base["initialLookbackDays"] = spec.initial_lookback_days
    if spec.harness_connections is not None:
        normalized: list[JsonValue] = []
        for item in spec.harness_connections:
            src = _extract_str(item, "source")
            via = _extract_str(item, "via")
            if not src or not via:
                return fail(
                    "Each harness_connections entry must specify non-empty 'source' and 'via' strings.",
                    ErrorCategory.VALIDATION,
                )
            normalized.append({"source": src, "via": via})
        base["harnessConnections"] = normalized
    else:
        base.setdefault("harnessConnections", [])
    base["standaloneSources"] = (
        [s.strip() for s in spec.standalone_sources if s.strip()]
        if spec.standalone_sources is not None
        else base.get("standaloneSources", [])
    )
    base["disabledSources"] = (
        [s.strip() for s in spec.disabled_sources if s.strip()]
        if spec.disabled_sources is not None
        else base.get("disabledSources", [])
    )
    return ok(base)


def _resolve_candidate_vault(
    vault_root: str | None,
    overrides: ServerOverrides,
    user_v2: Mapping[str, JsonValue],
) -> Result[Path | None]:
    raw: Path | None = None
    label = "vault_root"
    if vault_root is not None:
        if not vault_root.strip():
            return fail("vault_root must be a non-empty absolute path.", ErrorCategory.VALIDATION)
        raw = Path(vault_root.strip()).expanduser()
    elif overrides.vault_root is not None:
        raw = overrides.vault_root.expanduser()
    else:
        stored = _extract_str(user_v2, "defaultVaultRoot") or _extract_str(user_v2, "vaultRoot")
        if stored is None:
            return ok(None)
        raw = Path(stored).expanduser()
        label = "defaultVaultRoot"
    if not raw.is_absolute():
        return fail(f"{label} must be an absolute path.", ErrorCategory.VALIDATION)
    resolved = raw.resolve()
    if is_agent_runtime_root(resolved):
        return fail(
            f"Refusing to use agent runtime root {resolved.as_posix()} "
            "(contains SOUL.md and IDENTITY.md) as a Daily Tasks vault; pass the user's vault_root.",
            ErrorCategory.VALIDATION,
        )
    return ok(resolved)


def inspect_setup_status(
    store: ProfileStore,
    templates: TemplateSynchronizer,
    overrides: ServerOverrides,
    vault_root: str | None,
    status_tool: str,
) -> Result[dict[str, JsonValue]]:
    """Inspect `user_home` / `repo_root` Schema Version 2 `config.json`, templates, and all four setup gates."""
    user_raw = store.read_raw(store.user_profile_path)
    if not user_raw.ok:
        return fail(user_raw.message, user_raw.category)
    user_doc = user_raw.value
    user_v2 = user_doc if isinstance(user_doc, dict) and user_doc.get("schema_version") == 2 else {}

    vault_res = _resolve_candidate_vault(vault_root, overrides, user_v2)
    if not vault_res.ok:
        return fail(vault_res.message, vault_res.category)
    resolved_vault = vault_res.value
    host_tz = detect_host_timezone()
    host_tz_ambiguous = host_tz in {None, "UTC", "Etc/UTC"}

    if resolved_vault is None:
        return ok(
            {
                "tool": status_tool,
                "status": "ok",
                "message": "Daily Tasks setup is incomplete: no vault_root is bound yet.",
                "payload": {
                    "setup_complete": False,
                    "vault_bound": False,
                    "user_config_path": store.user_config_path.as_posix(),
                    "user_profile_path": store.user_profile_path.as_posix(),
                    "user_profile_v2_present": bool(user_v2),
                    "host_timezone": host_tz,
                    "host_timezone_needs_user_confirmation": host_tz_ambiguous,
                    "missing_gates": ["vault_root_unbound", "schema_v2_profiles", "templates_baseline", "sources"],
                    "next_action": (
                        "Ask the user which absolute vault directory to bind as vault_root, confirm identity, "
                        "IANA timezone, and Email/Chat connector choices, then call "
                        "daily_tasks_configure_vault(confirmed=true, ...)."
                    ),
                },
            }
        )

    layered_res = store.read_layered(resolved_vault)
    layered = layered_res.value if layered_res.ok else {}
    settings_check = resolve_server_settings(
        resolved_vault,
        ServerOverrides(
            config_dir=store.user_dir,
            repo_root=overrides.repo_root,
            runtime_root=overrides.runtime_root,
        ),
    )
    tpl_check = templates.validate_baseline(
        resolved_vault, store.home_root, store.templates_updates_path, layered.get("templates")
    )
    if not tpl_check.ok:
        return fail(tpl_check.message, tpl_check.category)
    templates_valid = tpl_check.value
    sources_valid = _sources_valid(layered.get("sources"))

    missing_gates: list[str] = []
    if not settings_check.ok:
        missing_gates.append(f"schema_v2_profiles ({settings_check.message})")
    if not templates_valid:
        missing_gates.append("templates_baseline")
    if not sources_valid:
        missing_gates.append("sources_configuration")

    setup_complete = len(missing_gates) == 0
    layout = (
        "para" if any((resolved_vault / f).is_dir() for f in ("1-projects", "2-areas", "3-resources")) else "standard"
    )
    payload: dict[str, JsonValue] = {
        "setup_complete": setup_complete,
        "vault_bound": True,
        "vault_root": resolved_vault.as_posix(),
        "vault_exists": resolved_vault.is_dir(),
        "detected_layout": layout,
        "gates": {
            "mcp_server_live": True,
            "schema_v2_profiles_valid": settings_check.ok,
            "templates_baseline_present": templates_valid,
            "sources_configured": sources_valid,
        },
        "missing_gates": list(missing_gates),
        "user_config_path": store.user_config_path.as_posix(),
        "user_profile_path": store.user_profile_path.as_posix(),
        "host_timezone": host_tz,
        "host_timezone_needs_user_confirmation": host_tz_ambiguous,
        "discovered_existing_templates": dict(templates.discover_existing(resolved_vault, _DEFAULT_TEMPLATES_DIR)),
        "proposed_settings": {
            "vault_root": resolved_vault.as_posix(),
            "user_name": _extract_str(layered, "user", "name"),
            "user_email": _extract_str(layered, "user", "email"),
            "timezone": _extract_str(layered, "timezone") or (None if host_tz_ambiguous else host_tz),
            "priorities": list(_extract_str_list(layered.get("priorities"))),
            "projects_root": _extract_str(layered, "projectsRoot") or DEFAULT_PROJECTS_ROOT,
            "daily_plans_relative": _extract_str(layered, "dailyPlansRelative") or DEFAULT_DAILY_PLANS_RELATIVE,
            "templates_dir": _DEFAULT_TEMPLATES_DIR,
            "initial_lookback_days": 7,
        },
        "next_action": (
            "All four setup gates are satisfied; proceed directly to the requested workflow."
            if setup_complete
            else "Present proposed_settings and the discovered Email/Chat connector inventory table to the user. "
            "After explicit user confirmation, call daily_tasks_configure_vault with confirmed=true."
        ),
    }
    status_msg = (
        f"Daily Tasks setup is complete for {resolved_vault.as_posix()}."
        if setup_complete
        else f"Daily Tasks setup is incomplete for {resolved_vault.as_posix()}: {', '.join(missing_gates)}."
    )
    return ok({"tool": status_tool, "status": "ok", "message": status_msg, "payload": payload})
