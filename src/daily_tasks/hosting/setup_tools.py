"""Responsibility: Inspect setup gates and persist Schema Version 2 Daily Tasks configuration in user_home.
Public interface:
`-- SetupTools
    +-- CONFIGURE_TOOL
    +-- STATUS_TOOL
    +-- configure_vault(spec)
    +-- new(overrides, clock, plugin_version, assets_dir)
    `-- setup_status(vault_root)
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Final, final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue, TypeAdapter

from daily_tasks.core.planning.tool_result_error import ToolResultError
from daily_tasks.hosting.detect_host_timezone import valid_iana_timezone
from daily_tasks.hosting.inspect_setup_status import build_sources_config, inspect_setup_status
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

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION_STATUS: Final = "mcp.setup_status"
_OPERATION_CONFIGURE: Final = "mcp.configure_vault"
_DEFAULT_TEMPLATES_DIR: Final = "./3-resources/templates"
_ERROR: Final[TypeAdapter[ToolResultError]] = TypeAdapter(ToolResultError)


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


@final
class SetupTools:
    """Entity-first `SetupHandler` writing Schema Version 2 profiles in `user_home` with zero `.nyssa-ai/` in vaults."""

    STATUS_TOOL: ClassVar[str] = "daily_tasks_setup_status"
    CONFIGURE_TOOL: ClassVar[str] = "daily_tasks_configure_vault"

    def __init__(
        self,
        overrides: ServerOverrides,
        clock: Callable[[], datetime],
        plugin_version: str = "0.11.2",
        assets_dir: Path | None = None,
    ) -> None:
        """Store server overrides, UTC clock, and template synchronizer."""
        self._overrides = overrides
        self._templates = TemplateSynchronizer(clock=clock, plugin_version=plugin_version, assets_dir=assets_dir)

    def _store(self) -> ProfileStore:
        return ProfileStore(config_dir=self._overrides.config_dir, repo_root=self._overrides.repo_root)

    def _failed(self, tool: str, message: str, category: ErrorCategory | str) -> dict[str, JsonValue]:
        code = str(category)
        _LOGGER.warning("setup tool error", extra={"operation": tool, "fields": {"code": code}})
        err = ToolResultError(
            tool=tool,
            status="error",
            session_id=None,
            screen_id=None,
            stage=None,
            message=message,
            code=code,
            payload=None,
        )
        dumped: dict[str, JsonValue] = _ERROR.dump_python(err, mode="json")
        return dumped

    def _resolve_vault(self, vault_root: str | None, existing_v2: Mapping[str, JsonValue]) -> Result[Path]:
        raw: Path | None = None
        label = "vault_root"
        if vault_root is not None:
            if not vault_root.strip():
                return fail("vault_root must be a non-empty absolute path.", ErrorCategory.VALIDATION)
            raw = Path(vault_root.strip()).expanduser()
        elif self._overrides.vault_root is not None:
            raw = self._overrides.vault_root.expanduser()
        else:
            stored = _extract_str(existing_v2, "defaultVaultRoot") or _extract_str(existing_v2, "vaultRoot")
            if stored is not None:
                raw = Path(stored).expanduser()
                label = "defaultVaultRoot"
        if raw is None:
            return fail("vault_root is required for vault-scope configuration.", ErrorCategory.VALIDATION)
        if not raw.is_absolute():
            return fail(f"{label} must be an absolute path.", ErrorCategory.VALIDATION)
        resolved = raw.resolve()
        if is_agent_runtime_root(resolved):
            return fail(
                f"Refusing to use agent runtime root {resolved.as_posix()} "
                "(contains SOUL.md and IDENTITY.md) as a Daily Tasks vault; pass the user's vault_root.",
                ErrorCategory.VALIDATION,
            )
        if not resolved.is_dir():
            return fail(
                f"vault_root {resolved.as_posix()} does not exist or is not a directory.",
                ErrorCategory.VALIDATION,
            )
        return ok(resolved)

    def setup_status(self, vault_root: str | None = None) -> dict[str, JsonValue]:
        """Inspect `user_home` / `repo_root` Schema Version 2 profiles, templates, and all four setup gates."""
        inspected = inspect_setup_status(self._store(), self._templates, self._overrides, vault_root, self.STATUS_TOOL)
        if not inspected.ok:
            return self._failed(self.STATUS_TOOL, inspected.message, inspected.category)
        _LOGGER.info("setup status inspected", extra={"operation": _OPERATION_STATUS})
        return inspected.value

    def configure_vault(self, spec: VaultSetupSpec) -> dict[str, JsonValue]:
        """Persist validated Schema Version 2 configuration in `user_home` and seed vault Markdown templates."""
        if not spec.confirmed:
            return self._failed(
                self.CONFIGURE_TOOL,
                "Refusing to write Daily Tasks configuration without confirmed=true.",
                ErrorCategory.FORBIDDEN,
            )
        if spec.scope not in {"vault", "personal"}:
            return self._failed(self.CONFIGURE_TOOL, "scope must be 'vault' or 'personal'.", ErrorCategory.VALIDATION)
        if spec.initial_lookback_days <= 0:
            return self._failed(
                self.CONFIGURE_TOOL,
                "initial_lookback_days must be a positive integer.",
                ErrorCategory.VALIDATION,
            )

        store = self._store()
        existing_res = store.read_raw(store.user_profile_path)
        if not existing_res.ok:
            return self._failed(self.CONFIGURE_TOOL, existing_res.message, existing_res.category)
        existing_doc = existing_res.value
        existing_v2 = existing_doc if isinstance(existing_doc, dict) and existing_doc.get("schema_version") == 2 else {}

        resolved_email = (spec.user_email.strip() if spec.user_email else None) or _extract_str(
            existing_v2, "user", "email"
        )
        if not resolved_email or "@" not in resolved_email:
            return self._failed(
                self.CONFIGURE_TOOL,
                "A valid user_email is required to configure Daily Tasks.",
                ErrorCategory.VALIDATION,
            )
        resolved_name = (
            (spec.user_name.strip() if spec.user_name else None)
            or _extract_str(existing_v2, "user", "name")
            or resolved_email
        )
        resolved_tz = (spec.timezone.strip() if spec.timezone else None) or _extract_str(existing_v2, "timezone")
        if not resolved_tz or not valid_iana_timezone(resolved_tz):
            return self._failed(
                self.CONFIGURE_TOOL,
                "timezone must be an explicit valid IANA timezone (e.g. 'America/Chicago', never 'system').",
                ErrorCategory.VALIDATION,
            )
        resolved_priorities: list[JsonValue] = (
            [p.strip() for p in spec.priorities if p.strip()]
            if spec.priorities is not None
            else [*_extract_str_list(existing_v2.get("priorities"))]
        )

        if spec.scope == "personal":
            personal_doc: dict[str, JsonValue] = {
                **existing_v2,
                "schema_version": 2,
                "user": {"name": resolved_name, "email": resolved_email},
                "timezone": resolved_tz,
                "priorities": resolved_priorities,
            }
            written = store.write_user_profile(personal_doc)
            if not written.ok:
                return self._failed(self.CONFIGURE_TOOL, written.message, written.category)
            return {
                "tool": self.CONFIGURE_TOOL,
                "status": "ok",
                "message": f"Saved personal Schema Version 2 profile at {store.user_profile_path.as_posix()}.",
                "payload": {
                    "scope": "personal",
                    "user_profile_path": store.user_profile_path.as_posix(),
                    "timezone": resolved_tz,
                },
            }

        vault_res = self._resolve_vault(spec.vault_root, existing_v2)
        if not vault_res.ok:
            return self._failed(self.CONFIGURE_TOOL, vault_res.message, vault_res.category)
        resolved_vault = vault_res.value
        vault_posix = resolved_vault.as_posix()

        vaults_raw = existing_v2.get("vaults")
        vaults_map: dict[str, JsonValue] = dict(vaults_raw) if isinstance(vaults_raw, dict) else {}
        entry_raw = vaults_map.get(vault_posix)
        existing_entry: dict[str, JsonValue] = dict(entry_raw) if isinstance(entry_raw, dict) else {}

        eff_projects = (
            (spec.projects_root.strip() if spec.projects_root else None)
            or _extract_str(existing_entry, "projectsRoot")
            or DEFAULT_PROJECTS_ROOT
        )
        eff_plans = (
            (spec.daily_plans_relative.strip() if spec.daily_plans_relative else None)
            or _extract_str(existing_entry, "dailyPlansRelative")
            or DEFAULT_DAILY_PLANS_RELATIVE
        )
        tpl_raw = (spec.templates_dir.strip() if spec.templates_dir else None) or _DEFAULT_TEMPLATES_DIR
        tpl_rel = Path(tpl_raw[2:] if tpl_raw.startswith("./") else tpl_raw)
        if tpl_rel.is_absolute() or ".." in tpl_rel.parts or ".nyssa-ai" in tpl_rel.parts:
            return self._failed(
                self.CONFIGURE_TOOL,
                "templates_dir must stay within vault_root and outside .nyssa-ai/.",
                ErrorCategory.VALIDATION,
            )

        existing_tpl_raw = existing_entry.get("templates") or existing_v2.get("templates")
        existing_tpl = existing_tpl_raw if isinstance(existing_tpl_raw, dict) else {}
        tpl_sync = self._templates.sync(
            resolved_vault,
            (resolved_vault / tpl_rel).resolve(),
            tpl_rel,
            store.templates_updates_path,
            existing_tpl,
        )
        if not tpl_sync.ok:
            return self._failed(self.CONFIGURE_TOOL, tpl_sync.message, tpl_sync.category)
        registered_templates, seeded_files, reused_files, updates_path = tpl_sync.value

        sources_res = build_sources_config(
            existing_entry.get("sources") or existing_v2.get("sources"),
            spec,
        )
        if not sources_res.ok:
            return self._failed(self.CONFIGURE_TOOL, sources_res.message, sources_res.category)

        vaults_map[vault_posix] = {
            "vaultRoot": vault_posix,
            "projectsRoot": eff_projects,
            "dailyPlansRelative": eff_plans,
            "sources": sources_res.value,
            "templates": registered_templates,
        }
        user_doc_out: dict[str, JsonValue] = {
            **existing_v2,
            "schema_version": 2,
            "user": {"name": resolved_name, "email": resolved_email},
            "timezone": resolved_tz,
            "priorities": resolved_priorities,
            "projectsRoot": eff_projects,
            "dailyPlansRelative": eff_plans,
            "sources": sources_res.value,
            "templates": registered_templates,
            "vaults": vaults_map,
        }
        if spec.set_default_vault:
            user_doc_out["defaultVaultRoot"] = vault_posix

        check = resolve_server_settings(
            resolved_vault,
            ServerOverrides(
                projects_root=eff_projects,
                daily_plans_root=eff_plans,
                user_email=resolved_email,
                user_name=resolved_name,
                timezone=resolved_tz,
                initial_lookback_days=spec.initial_lookback_days,
                config_dir=store.user_dir,
            ),
        )
        if not check.ok:
            return self._failed(self.CONFIGURE_TOOL, check.message, check.category)

        written = store.write_user_profile(user_doc_out)
        if not written.ok:
            return self._failed(self.CONFIGURE_TOOL, written.message, written.category)

        _LOGGER.info(
            "vault configured",
            extra={"operation": _OPERATION_CONFIGURE, "fields": {"vault": resolved_vault.name}},
        )
        return {
            "tool": self.CONFIGURE_TOOL,
            "status": "ok",
            "message": f"Configured Schema Version 2 Daily Tasks vault at {vault_posix}.",
            "payload": {
                "scope": "vault",
                "setup_complete": True,
                "vault_root": vault_posix,
                "user_profile_path": store.user_profile_path.as_posix(),
                "templates_updates_path": updates_path.as_posix(),
                "timezone": resolved_tz,
                "projects_root": check.value.projects_root.as_posix(),
                "daily_plans_root": check.value.daily_plans_root.as_posix(),
                "runtime_root": check.value.runtime_root.as_posix(),
                "templates": registered_templates,
                "seeded_template_files": [*seeded_files],
                "reused_template_files": [*reused_files],
                "default_vault_bound": spec.set_default_vault,
            },
        }
