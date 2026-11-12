"""Responsibility: Inspect and deterministically write Schema Version 2 Daily Tasks setup profiles and templates.
Public interface:
`-- SetupTools
    +-- CONFIGURE_TOOL
    +-- STATUS_TOOL
    +-- configure_workspace(...)
    +-- new(overrides, clock, plugin_version, assets_dir)
    `-- setup_status(workspace_root)

Deterministic MCP setup tools (`daily_tasks_setup_status`, `daily_tasks_configure_workspace`) so host agents
inspect v1/v2 state and persist user-confirmed Schema Version 2 profiles and template baselines without hand-editing.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Final, final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue, TypeAdapter

from daily_tasks.domain import ToolResultError
from daily_tasks.server.resolve_server_settings import is_agent_persona_workspace, resolve_server_settings
from daily_tasks.server.types import ServerOverrides

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION_STATUS: Final = "mcp.setup_status"
_OPERATION_CONFIGURE: Final = "mcp.configure_workspace"
_STATE_DIR_NAME: Final = Path(".nyssa-ai") / "daily-tasks"
_LEGACY_STATE_DIR_NAME: Final = Path(".nyssaai") / "daily-tasks"
_ERROR: Final[TypeAdapter[ToolResultError]] = TypeAdapter(ToolResultError)
_DEFAULT_ASSETS_DIR: Final = Path(__file__).resolve().parents[3] / "skills" / "daily-tasks" / "assets"

_TEMPLATE_SPECS: Final[tuple[tuple[str, str, tuple[str, ...], str], ...]] = (
    ("projectIndex", "project-index.md", ("daily-tasks-project-index.md", "project-index.md"), "project-index.md"),
    ("dailyPlan", "daily-plan.md", ("daily-tasks-daily-plan.md", "daily-plan.md"), "daily-plan.md"),
    ("milestone", "milestone.md", ("daily-tasks-milestone.md", "milestone.md"), "milestone.md"),
    ("task", "task.md", ("daily-tasks-task.md", "task.md"), "task.md"),
    (
        "planDayReview",
        "plan-day-select-tasks-screen.md",
        (
            "daily-tasks-plan-day-select-tasks-screen.md",
            "plan-day-select-tasks-screen.md",
            "daily-tasks-plan-day-review.md",
            "plan-day-review.md",
        ),
        "plan-day-review.md",
    ),
)
_AUXILIARY_ASSETS: Final[tuple[tuple[str, tuple[str, ...], str], ...]] = (
    ("blocker.md", ("daily-tasks-blocker.md", "blocker.md"), "blocker.md"),
)


def _sha256_text(content: str) -> str:
    normalized = content.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _valid_iana_timezone(value: str | None) -> bool:
    if not value or value.strip() == "system":
        return False
    try:
        ZoneInfo(value.strip())
    except (ZoneInfoNotFoundError, ValueError):
        return False
    return True


def _detect_host_timezone() -> str | None:
    env_tz = os.environ.get("TZ", "").strip()
    if _valid_iana_timezone(env_tz):
        return env_tz
    localtime = Path("/etc/localtime")
    if localtime.is_symlink():
        try:
            resolved = localtime.resolve().as_posix()
        except OSError:
            resolved = ""
        marker = "/zoneinfo/"
        if marker in resolved:
            candidate = resolved.split(marker, 1)[1]
            if _valid_iana_timezone(candidate):
                return candidate
    etc_tz = Path("/etc/timezone")
    if etc_tz.is_file():
        try:
            candidate = etc_tz.read_text(encoding="utf-8").strip()
        except OSError:
            candidate = ""
        if _valid_iana_timezone(candidate):
            return candidate
    return None


def _read_raw_json_object(path: Path) -> Result[dict[str, JsonValue] | None]:
    if path.is_symlink():
        return fail(f"Configuration file at {path.as_posix()} must not be a symlink.", ErrorCategory.VALIDATION)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ok(None)
    except OSError as exc:
        return fail(f"Unable to read {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    try:
        parsed = json.loads(raw_text)
    except ValueError as exc:
        return fail(f"Malformed JSON in {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    if not isinstance(parsed, dict):
        return fail(f"Configuration file at {path.as_posix()} must contain a JSON object.", ErrorCategory.VALIDATION)
    return ok(parsed)


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


def _detect_layout(workspace: Path) -> tuple[str, str, str, str]:
    if any((workspace / folder).is_dir() for folder in ("1-projects", "2-areas", "3-resources")):
        return ("para", "1-projects", "2-areas/daily-plans", "./3-resources/templates")
    return ("standard", "projects", "daily-plans", "./templates")


def _resolve_template_path(workspace: Path, user_home: Path, pointer: str) -> Path | None:
    trimmed = pointer.strip()
    if not trimmed:
        return None
    if trimmed.startswith("./"):
        rel = Path(trimmed[2:])
        if ".." in rel.parts:
            return None
        resolved = (workspace / rel).resolve()
        return resolved if resolved.is_relative_to(workspace) else None
    if trimmed.startswith("~/"):
        rel = Path(trimmed[2:])
        if ".." in rel.parts:
            return None
        return (user_home / rel).resolve()
    candidate = Path(trimmed)
    return candidate.resolve() if candidate.is_absolute() else (workspace / candidate).resolve()


def _write_json_file(path: Path, payload: Mapping[str, JsonValue], private: bool) -> Result[None]:
    if path.exists() and path.is_symlink():
        return fail(f"Refusing to write through symlink at {path.as_posix()}.", ErrorCategory.VALIDATION)
    try:
        parent_existed = path.parent.exists()
        path.parent.mkdir(parents=True, exist_ok=True)
        if private and not parent_existed and os.name == "posix":
            path.parent.chmod(0o700)
        file_existed = path.exists()
        encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
        path.write_text(encoded, encoding="utf-8", newline="\n")
        if private and not file_existed and os.name == "posix":
            path.chmod(0o600)
    except OSError as exc:
        return fail(f"Unable to write {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    return ok(None)


@final
class SetupTools:
    """Inspect setup gates and deterministically write Schema Version 2 profiles and workspace templates."""

    STATUS_TOOL: ClassVar[str] = "daily_tasks_setup_status"
    CONFIGURE_TOOL: ClassVar[str] = "daily_tasks_configure_workspace"

    def __init__(
        self,
        overrides: ServerOverrides,
        clock: Callable[[], datetime],
        plugin_version: str = "0.11.0",
        assets_dir: Path | None = None,
    ) -> None:
        """Store server overrides, UTC clock, plugin version, and bundled template assets directory."""
        self._overrides = overrides
        self._clock = clock
        self._plugin_version = plugin_version
        self._assets_dir = assets_dir if assets_dir is not None else _DEFAULT_ASSETS_DIR

    def _user_paths(self) -> tuple[Path, Path | None, Path]:
        if self._overrides.config_dir is not None:
            user_dir = self._overrides.config_dir.expanduser().resolve()
            if user_dir.name == "daily-tasks" and user_dir.parent.name == ".nyssa-ai":
                home_root = user_dir.parent.parent
                legacy = home_root / _LEGACY_STATE_DIR_NAME / "profile.json"
                return user_dir, legacy, home_root
            return user_dir, None, Path.home()
        home_root = Path.home()
        return home_root / _STATE_DIR_NAME, home_root / _LEGACY_STATE_DIR_NAME / "profile.json", home_root

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

    def _resolve_candidate_workspace(
        self,
        workspace_root: str | None,
        user_v2: Mapping[str, JsonValue],
    ) -> Result[Path | None]:
        if workspace_root is not None:
            trimmed = workspace_root.strip()
            if not trimmed:
                return fail("workspace_root must be a non-empty absolute path.", ErrorCategory.VALIDATION)
            candidate = Path(trimmed).expanduser()
            if not candidate.is_absolute():
                return fail("workspace_root must be an absolute path.", ErrorCategory.VALIDATION)
            resolved = candidate.resolve()
            if is_agent_persona_workspace(resolved):
                return fail(
                    f"Refusing to use agent persona workspace {resolved.as_posix()} "
                    "(contains SOUL.md and IDENTITY.md) as a Daily Tasks vault; pass the user's vault workspace_root.",
                    ErrorCategory.VALIDATION,
                )
            return ok(resolved)
        if self._overrides.workspace_root is not None:
            resolved = self._overrides.workspace_root.expanduser().resolve()
            if is_agent_persona_workspace(resolved):
                return fail(
                    f"Refusing to use agent persona workspace {resolved.as_posix()} "
                    "(contains SOUL.md and IDENTITY.md) as a Daily Tasks vault.",
                    ErrorCategory.VALIDATION,
                )
            return ok(resolved)
        default_ws = _extract_str(user_v2, "defaultWorkspaceRoot") or _extract_str(user_v2, "workspaceRoot")
        if default_ws is None:
            return ok(None)
        candidate = Path(default_ws).expanduser()
        if not candidate.is_absolute():
            return fail("defaultWorkspaceRoot in user profile.json must be an absolute path.", ErrorCategory.VALIDATION)
        resolved = candidate.resolve()
        if is_agent_persona_workspace(resolved):
            return fail(
                f"Stored defaultWorkspaceRoot {resolved.as_posix()} is an agent persona workspace; re-run Setup.",
                ErrorCategory.VALIDATION,
            )
        return ok(resolved)

    def setup_status(self, workspace_root: str | None = None) -> dict[str, JsonValue]:
        """Inspect user/workspace v2 profiles, legacy v1 profiles, templates, and all four setup gates."""
        user_dir, legacy_user_path, home_root = self._user_paths()
        user_profile_path = user_dir / "profile.json"
        user_raw = _read_raw_json_object(user_profile_path)
        if not user_raw.ok:
            return self._failed(self.STATUS_TOOL, user_raw.message, user_raw.category)
        user_doc = user_raw.value
        user_v2 = user_doc if isinstance(user_doc, dict) and user_doc.get("schema_version") == 2 else {}

        legacy_user_doc: dict[str, JsonValue] | None = None
        if legacy_user_path is not None and legacy_user_path.exists():
            leg_res = _read_raw_json_object(legacy_user_path)
            if not leg_res.ok:
                return self._failed(self.STATUS_TOOL, leg_res.message, leg_res.category)
            legacy_user_doc = leg_res.value

        ws_res = self._resolve_candidate_workspace(workspace_root, user_v2)
        if not ws_res.ok:
            return self._failed(self.STATUS_TOOL, ws_res.message, ws_res.category)
        resolved_ws = ws_res.value

        host_tz = _detect_host_timezone()
        host_tz_ambiguous = host_tz in {None, "UTC", "Etc/UTC"}

        if resolved_ws is None:
            payload_no_ws: dict[str, JsonValue] = {
                "setup_complete": False,
                "workspace_bound": False,
                "user_profile_path": user_profile_path.as_posix(),
                "user_profile_v2_present": bool(user_v2),
                "legacy_user_v1_path": legacy_user_path.as_posix()
                if legacy_user_doc is not None and legacy_user_path
                else None,
                "legacy_user_v1": legacy_user_doc,
                "host_timezone": host_tz,
                "host_timezone_needs_user_confirmation": host_tz_ambiguous,
                "missing_gates": ["workspace_root_unbound", "schema_v2_profiles", "templates_baseline", "sources"],
                "next_action": (
                    "Ask the user which absolute vault/workspace directory to bind as workspace_root "
                    "(or pass the authorized vault path to daily_tasks_setup_status), confirm identity, IANA timezone, "
                    "and Email/Chat connector choices, then call daily_tasks_configure_workspace(confirmed=true, ...)."
                ),
            }
            return {
                "tool": self.STATUS_TOOL,
                "status": "ok",
                "message": "Daily Tasks setup is incomplete: no workspace_root is bound yet.",
                "payload": payload_no_ws,
            }

        ws_profile_path = resolved_ws / _STATE_DIR_NAME / "profile.json"
        ws_legacy_path = resolved_ws / _LEGACY_STATE_DIR_NAME / "profile.json"
        ws_raw = _read_raw_json_object(ws_profile_path)
        if not ws_raw.ok:
            return self._failed(self.STATUS_TOOL, ws_raw.message, ws_raw.category)
        ws_doc = ws_raw.value
        ws_v2 = ws_doc if isinstance(ws_doc, dict) and ws_doc.get("schema_version") == 2 else {}

        legacy_ws_doc: dict[str, JsonValue] | None = None
        if ws_legacy_path.exists():
            ws_leg_res = _read_raw_json_object(ws_legacy_path)
            if not ws_leg_res.ok:
                return self._failed(self.STATUS_TOOL, ws_leg_res.message, ws_leg_res.category)
            legacy_ws_doc = ws_leg_res.value

        layout, default_projects, default_plans, default_templates_dir = _detect_layout(resolved_ws)
        settings_check = resolve_server_settings(resolved_ws, ServerOverrides(config_dir=user_dir))

        updates_path = resolved_ws / _STATE_DIR_NAME / "templates" / "updates.json"
        updates_raw = _read_raw_json_object(updates_path)
        if not updates_raw.ok:
            return self._failed(self.STATUS_TOOL, updates_raw.message, updates_raw.category)
        templates_map = ws_v2.get("templates")
        templates_valid = updates_raw.value is not None and isinstance(templates_map, dict)
        if templates_valid and isinstance(templates_map, dict):
            for kind, _, _, _ in _TEMPLATE_SPECS:
                pointer = templates_map.get(kind)
                if pointer is None:
                    continue
                if not isinstance(pointer, str):
                    templates_valid = False
                    break
                target = _resolve_template_path(resolved_ws, home_root, pointer)
                if target is None or not target.is_file():
                    templates_valid = False
                    break

        discovered_templates: dict[str, str] = {}
        candidate_tpl_dir = resolved_ws / Path(default_templates_dir[2:])
        if candidate_tpl_dir.is_dir():
            rel_prefix = default_templates_dir.rstrip("/")
            for kind, _, existing_names, _ in _TEMPLATE_SPECS:
                for fname in existing_names:
                    if (candidate_tpl_dir / fname).is_file():
                        discovered_templates[kind] = f"{rel_prefix}/{fname}"
                        break

        sources_map = ws_v2.get("sources")
        lookback_val = sources_map.get("initialLookbackDays") if isinstance(sources_map, dict) else None
        sources_valid = (
            isinstance(sources_map, dict)
            and isinstance(lookback_val, int)
            and not isinstance(lookback_val, bool)
            and lookback_val > 0
            and any(
                k in sources_map
                for k in (
                    "harnessConnections",
                    "standaloneSources",
                    "disabledSources",
                    "gmail",
                    "slack",
                    "outlook",
                    "teams",
                )
            )
        )

        missing_gates: list[str] = []
        if not settings_check.ok:
            missing_gates.append(f"schema_v2_profiles ({settings_check.message})")
        if not templates_valid:
            missing_gates.append("templates_baseline")
        if not sources_valid:
            missing_gates.append("sources_configuration")

        setup_complete = len(missing_gates) == 0
        legacy_merged: dict[str, JsonValue] = {**(legacy_user_doc or {}), **(legacy_ws_doc or {})}
        proposed_name = (
            _extract_str(ws_v2, "user", "name")
            or _extract_str(user_v2, "user", "name")
            or _extract_str(legacy_merged, "user", "name")
        )
        proposed_email = (
            _extract_str(ws_v2, "user", "email")
            or _extract_str(user_v2, "user", "email")
            or _extract_str(legacy_merged, "user", "email")
        )
        proposed_tz = (
            _extract_str(ws_v2, "timezone")
            or _extract_str(user_v2, "timezone")
            or _extract_str(legacy_merged, "timezone")
            or (None if host_tz_ambiguous else host_tz)
        )
        proposed_priorities = (
            _extract_str_list(ws_v2.get("priorities"))
            or _extract_str_list(user_v2.get("priorities"))
            or _extract_str_list(legacy_merged.get("priorities"))
        )
        proposed_projects = (
            _extract_str(ws_v2, "projectsRoot") or _extract_str(legacy_merged, "projectsRoot") or default_projects
        )
        proposed_plans = (
            _extract_str(ws_v2, "dailyPlansRelative")
            or _extract_str(legacy_merged, "dailyPlansRelative")
            or default_plans
        )

        payload: dict[str, JsonValue] = {
            "setup_complete": setup_complete,
            "workspace_bound": True,
            "workspace_root": resolved_ws.as_posix(),
            "workspace_exists": resolved_ws.is_dir(),
            "detected_layout": layout,
            "gates": {
                "mcp_server_live": True,
                "schema_v2_profiles_valid": settings_check.ok,
                "templates_baseline_present": templates_valid,
                "sources_configured": sources_valid,
            },
            "missing_gates": list(missing_gates),
            "user_profile_path": user_profile_path.as_posix(),
            "workspace_profile_path": ws_profile_path.as_posix(),
            "legacy_v1_detected": legacy_ws_doc is not None or legacy_user_doc is not None,
            "legacy_workspace_v1_path": ws_legacy_path.as_posix() if legacy_ws_doc is not None else None,
            "legacy_workspace_v1": legacy_ws_doc,
            "legacy_user_v1_path": legacy_user_path.as_posix()
            if legacy_user_doc is not None and legacy_user_path
            else None,
            "legacy_user_v1": legacy_user_doc,
            "host_timezone": host_tz,
            "host_timezone_needs_user_confirmation": host_tz_ambiguous,
            "discovered_existing_templates": dict(discovered_templates),
            "proposed_settings": {
                "workspace_root": resolved_ws.as_posix(),
                "user_name": proposed_name,
                "user_email": proposed_email,
                "timezone": proposed_tz,
                "priorities": list(proposed_priorities),
                "projects_root": proposed_projects,
                "daily_plans_relative": proposed_plans,
                "templates_dir": default_templates_dir,
                "initial_lookback_days": 7,
            },
            "next_action": (
                "All four setup gates are satisfied; proceed directly to the requested workflow."
                if setup_complete
                else "Present proposed_settings (noting any legacy_v1 migration values) and the discovered Email/Chat "
                "connector inventory table to the user. After the user explicitly confirms identity, IANA timezone, "
                "storage paths, and connector selections, call daily_tasks_configure_workspace with confirmed=true."
            ),
        }
        status_msg = (
            f"Daily Tasks setup is complete for {resolved_ws.as_posix()}."
            if setup_complete
            else f"Daily Tasks setup is incomplete for {resolved_ws.as_posix()}: {', '.join(missing_gates)}."
        )
        _LOGGER.info(
            "setup status inspected", extra={"operation": _OPERATION_STATUS, "fields": {"complete": setup_complete}}
        )
        return {"tool": self.STATUS_TOOL, "status": "ok", "message": status_msg, "payload": payload}

    def configure_workspace(
        self,
        confirmed: bool,
        scope: str = "workspace",
        workspace_root: str | None = None,
        user_name: str | None = None,
        user_email: str | None = None,
        timezone: str | None = None,
        priorities: Sequence[str] | None = None,
        projects_root: str | None = None,
        daily_plans_relative: str | None = None,
        templates_dir: str | None = None,
        harness_connections: Sequence[Mapping[str, JsonValue]] | None = None,
        standalone_sources: Sequence[str] | None = None,
        disabled_sources: Sequence[str] | None = None,
        initial_lookback_days: int = 7,
        set_default_workspace: bool = True,
    ) -> dict[str, JsonValue]:
        """Persist validated Schema Version 2 user/workspace profiles and workspace template baselines."""
        if not confirmed:
            return self._failed(
                self.CONFIGURE_TOOL,
                "Refusing to write Daily Tasks configuration without confirmed=true. "
                "Present the proposed settings and connector inventory to the user and obtain explicit confirmation.",
                ErrorCategory.FORBIDDEN,
            )
        if scope not in {"workspace", "personal"}:
            return self._failed(
                self.CONFIGURE_TOOL,
                "scope must be 'workspace' or 'personal'.",
                ErrorCategory.VALIDATION,
            )
        if initial_lookback_days <= 0:
            return self._failed(
                self.CONFIGURE_TOOL,
                "initial_lookback_days must be a positive integer.",
                ErrorCategory.VALIDATION,
            )

        user_dir, _, _ = self._user_paths()
        user_profile_path = user_dir / "profile.json"
        existing_user_res = _read_raw_json_object(user_profile_path)
        if not existing_user_res.ok:
            return self._failed(self.CONFIGURE_TOOL, existing_user_res.message, existing_user_res.category)
        existing_user_doc = existing_user_res.value
        existing_user_v2 = (
            existing_user_doc
            if isinstance(existing_user_doc, dict) and existing_user_doc.get("schema_version") == 2
            else {}
        )

        resolved_email = (user_email.strip() if user_email else None) or _extract_str(existing_user_v2, "user", "email")
        if not resolved_email or "@" not in resolved_email:
            return self._failed(
                self.CONFIGURE_TOOL,
                "A valid user_email is required to configure Daily Tasks.",
                ErrorCategory.VALIDATION,
            )
        resolved_name = (
            (user_name.strip() if user_name else None)
            or _extract_str(existing_user_v2, "user", "name")
            or resolved_email
        )
        resolved_tz = (timezone.strip() if timezone else None) or _extract_str(existing_user_v2, "timezone")
        if not resolved_tz or not _valid_iana_timezone(resolved_tz):
            return self._failed(
                self.CONFIGURE_TOOL,
                "timezone must be an explicit valid IANA timezone (e.g. 'America/Chicago', never 'system').",
                ErrorCategory.VALIDATION,
            )
        resolved_priorities: list[JsonValue] = (
            [p.strip() for p in priorities if p.strip()]
            if priorities is not None
            else list(_extract_str_list(existing_user_v2.get("priorities")))
        )

        if scope == "personal":
            personal_doc: dict[str, JsonValue] = {
                **existing_user_v2,
                "schema_version": 2,
                "user": {"name": resolved_name, "email": resolved_email},
                "timezone": resolved_tz,
                "priorities": resolved_priorities,
            }
            write_user = _write_json_file(user_profile_path, personal_doc, private=True)
            if not write_user.ok:
                return self._failed(self.CONFIGURE_TOOL, write_user.message, write_user.category)
            _LOGGER.info(
                "personal profile configured",
                extra={"operation": _OPERATION_CONFIGURE, "fields": {"scope": "personal"}},
            )
            return {
                "tool": self.CONFIGURE_TOOL,
                "status": "ok",
                "message": f"Saved personal Schema Version 2 profile at {user_profile_path.as_posix()}.",
                "payload": {
                    "scope": "personal",
                    "user_profile_path": user_profile_path.as_posix(),
                    "timezone": resolved_tz,
                },
            }

        ws_res = self._resolve_candidate_workspace(workspace_root, existing_user_v2)
        if not ws_res.ok:
            return self._failed(self.CONFIGURE_TOOL, ws_res.message, ws_res.category)
        if ws_res.value is None:
            return self._failed(
                self.CONFIGURE_TOOL,
                "workspace_root is required for workspace-scope configuration.",
                ErrorCategory.VALIDATION,
            )
        resolved_ws = ws_res.value
        if not resolved_ws.is_dir():
            return self._failed(
                self.CONFIGURE_TOOL,
                f"workspace_root {resolved_ws.as_posix()} does not exist or is not a directory.",
                ErrorCategory.VALIDATION,
            )

        ws_profile_path = resolved_ws / _STATE_DIR_NAME / "profile.json"
        existing_ws_res = _read_raw_json_object(ws_profile_path)
        if not existing_ws_res.ok:
            return self._failed(self.CONFIGURE_TOOL, existing_ws_res.message, existing_ws_res.category)
        existing_ws_doc = existing_ws_res.value
        existing_ws_v2 = (
            existing_ws_doc if isinstance(existing_ws_doc, dict) and existing_ws_doc.get("schema_version") == 2 else {}
        )

        _, default_projects, default_plans, default_templates_dir = _detect_layout(resolved_ws)
        effective_projects = (
            (projects_root.strip() if projects_root else None)
            or _extract_str(existing_ws_v2, "projectsRoot")
            or default_projects
        )
        effective_plans = (
            (daily_plans_relative.strip() if daily_plans_relative else None)
            or _extract_str(existing_ws_v2, "dailyPlansRelative")
            or default_plans
        )
        effective_tpl_dir_raw = (templates_dir.strip() if templates_dir else None) or default_templates_dir
        normalized_tpl_rel = (
            effective_tpl_dir_raw[2:] if effective_tpl_dir_raw.startswith("./") else effective_tpl_dir_raw
        )
        tpl_rel_path = Path(normalized_tpl_rel)
        state_root = (resolved_ws / _STATE_DIR_NAME).resolve()
        if tpl_rel_path.is_absolute() or ".." in tpl_rel_path.parts:
            return self._failed(
                self.CONFIGURE_TOOL,
                "templates_dir must be a workspace-relative path without '..' traversal.",
                ErrorCategory.VALIDATION,
            )
        resolved_tpl_dir = (resolved_ws / tpl_rel_path).resolve()
        if not resolved_tpl_dir.is_relative_to(resolved_ws) or resolved_tpl_dir.is_relative_to(state_root):
            return self._failed(
                self.CONFIGURE_TOOL,
                "templates_dir must stay within workspace_root and outside .nyssa-ai/.",
                ErrorCategory.VALIDATION,
            )

        templates_result = self._seed_templates_and_baselines(
            resolved_ws, resolved_tpl_dir, tpl_rel_path, existing_ws_v2
        )
        if not templates_result.ok:
            return self._failed(self.CONFIGURE_TOOL, templates_result.message, templates_result.category)
        registered_templates, seeded_files, reused_files, updates_path = templates_result.value

        sources_payload = self._build_sources_payload(
            existing_ws_v2.get("sources"),
            harness_connections=harness_connections,
            standalone_sources=standalone_sources,
            disabled_sources=disabled_sources,
            initial_lookback_days=initial_lookback_days,
        )
        if not sources_payload.ok:
            return self._failed(self.CONFIGURE_TOOL, sources_payload.message, sources_payload.category)

        user_doc_out: dict[str, JsonValue] = {
            **existing_user_v2,
            "schema_version": 2,
            "user": {"name": resolved_name, "email": resolved_email},
            "timezone": resolved_tz,
            "priorities": resolved_priorities,
        }
        if set_default_workspace:
            user_doc_out["defaultWorkspaceRoot"] = resolved_ws.as_posix()

        ws_doc_out: dict[str, JsonValue] = {
            **existing_ws_v2,
            "schema_version": 2,
            "workspaceRoot": resolved_ws.as_posix(),
            "projectsRoot": effective_projects,
            "dailyPlansRelative": effective_plans,
            "user": {"name": resolved_name, "email": resolved_email},
            "timezone": resolved_tz,
            "priorities": resolved_priorities,
            "sources": sources_payload.value,
            "templates": registered_templates,
        }

        # Validate path containment before persisting workspace profile
        proj_path = Path(effective_projects).expanduser()
        if not proj_path.is_absolute() and ".." in proj_path.parts:
            return self._failed(
                self.CONFIGURE_TOOL,
                "projectsRoot relative path must not contain '..' traversal.",
                ErrorCategory.VALIDATION,
            )
        plans_path = Path(effective_plans).expanduser()
        if not plans_path.is_absolute() and ".." in plans_path.parts:
            return self._failed(
                self.CONFIGURE_TOOL,
                "dailyPlansRelative must stay within workspaceRoot and outside .nyssa-ai/.",
                ErrorCategory.VALIDATION,
            )
        resolved_plans = plans_path.resolve() if plans_path.is_absolute() else (resolved_ws / plans_path).resolve()
        if not resolved_plans.is_relative_to(resolved_ws) or resolved_plans.is_relative_to(state_root):
            return self._failed(
                self.CONFIGURE_TOOL,
                "dailyPlansRelative must stay within workspaceRoot and outside .nyssa-ai/.",
                ErrorCategory.VALIDATION,
            )

        write_user = _write_json_file(user_profile_path, user_doc_out, private=True)
        if not write_user.ok:
            return self._failed(self.CONFIGURE_TOOL, write_user.message, write_user.category)
        write_ws = _write_json_file(ws_profile_path, ws_doc_out, private=False)
        if not write_ws.ok:
            return self._failed(self.CONFIGURE_TOOL, write_ws.message, write_ws.category)

        verified = resolve_server_settings(resolved_ws, ServerOverrides(config_dir=user_dir))
        if not verified.ok:
            return self._failed(self.CONFIGURE_TOOL, verified.message, verified.category)

        _LOGGER.info(
            "workspace configured",
            extra={
                "operation": _OPERATION_CONFIGURE,
                "fields": {"workspace": resolved_ws.name, "seeded_templates": len(seeded_files)},
            },
        )
        seeded_json: list[JsonValue] = [*seeded_files]
        reused_json: list[JsonValue] = [*reused_files]
        return {
            "tool": self.CONFIGURE_TOOL,
            "status": "ok",
            "message": f"Configured Schema Version 2 Daily Tasks workspace at {resolved_ws.as_posix()}.",
            "payload": {
                "scope": "workspace",
                "setup_complete": True,
                "workspace_root": resolved_ws.as_posix(),
                "user_profile_path": user_profile_path.as_posix(),
                "workspace_profile_path": ws_profile_path.as_posix(),
                "templates_updates_path": updates_path.as_posix(),
                "timezone": resolved_tz,
                "projects_root": verified.value.projects_root.as_posix(),
                "daily_plans_root": verified.value.daily_plans_root.as_posix(),
                "templates": registered_templates,
                "seeded_template_files": seeded_json,
                "reused_template_files": reused_json,
                "default_workspace_bound": set_default_workspace,
            },
        }

    def _build_sources_payload(
        self,
        existing_sources: JsonValue,
        *,
        harness_connections: Sequence[Mapping[str, JsonValue]] | None,
        standalone_sources: Sequence[str] | None,
        disabled_sources: Sequence[str] | None,
        initial_lookback_days: int,
    ) -> Result[dict[str, JsonValue]]:
        base: dict[str, JsonValue] = dict(existing_sources) if isinstance(existing_sources, dict) else {}
        base["initialLookbackDays"] = initial_lookback_days
        if harness_connections is not None:
            normalized_conns: list[JsonValue] = []
            for item in harness_connections:
                src = _extract_str(item, "source")
                via = _extract_str(item, "via")
                if not src or not via:
                    return fail(
                        "Each harness_connections entry must specify non-empty 'source' and 'via' strings.",
                        ErrorCategory.VALIDATION,
                    )
                normalized_conns.append({"source": src, "via": via})
            base["harnessConnections"] = normalized_conns
        elif "harnessConnections" not in base:
            base["harnessConnections"] = []

        if standalone_sources is not None:
            base["standaloneSources"] = [s.strip() for s in standalone_sources if s.strip()]
        elif "standaloneSources" not in base:
            base["standaloneSources"] = []

        if disabled_sources is not None:
            base["disabledSources"] = [s.strip() for s in disabled_sources if s.strip()]
        elif "disabledSources" not in base:
            base["disabledSources"] = []

        return ok(base)

    def _seed_templates_and_baselines(
        self,
        workspace: Path,
        resolved_tpl_dir: Path,
        tpl_rel_path: Path,
        existing_ws_v2: Mapping[str, JsonValue],
    ) -> Result[tuple[dict[str, JsonValue], list[str], list[str], Path]]:
        if not self._assets_dir.is_dir():
            return fail(
                f"Bundled template assets directory is missing at {self._assets_dir.as_posix()}.",
                ErrorCategory.VALIDATION,
            )
        try:
            resolved_tpl_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return fail(
                f"Unable to create templates directory {resolved_tpl_dir.as_posix()}: {exc}", ErrorCategory.VALIDATION
            )

        existing_tpl_map = existing_ws_v2.get("templates")
        existing_pointers = existing_tpl_map if isinstance(existing_tpl_map, dict) else {}
        registered: dict[str, JsonValue] = {}
        seeded: list[str] = []
        reused: list[str] = []

        updates_path = workspace / _STATE_DIR_NAME / "templates" / "updates.json"
        updates_res = _read_raw_json_object(updates_path)
        if not updates_res.ok:
            return fail(updates_res.message, updates_res.category)
        existing_updates = updates_res.value if isinstance(updates_res.value, dict) else {}
        existing_policies = existing_updates.get("policies")
        policies: dict[str, JsonValue] = dict(existing_policies) if isinstance(existing_policies, dict) else {}
        existing_baselines = existing_updates.get("baselines")
        baselines: dict[str, JsonValue] = dict(existing_baselines) if isinstance(existing_baselines, dict) else {}
        now_iso = self._clock().strftime("%Y-%m-%dT%H:%M:%SZ")
        rel_prefix = f"./{tpl_rel_path.as_posix()}"

        for kind, asset_name, candidate_names, default_dest_name in _TEMPLATE_SPECS:
            asset_file = self._assets_dir / asset_name
            if not asset_file.is_file():
                return fail(f"Missing bundled template asset {asset_file.as_posix()}.", ErrorCategory.VALIDATION)
            bundled_text = asset_file.read_text(encoding="utf-8").replace("\r\n", "\n")
            policies.setdefault(kind, "ask")

            if kind in existing_pointers and existing_pointers[kind] is None:
                registered[kind] = None
                continue

            chosen_file: Path | None = None
            chosen_pointer: str | None = None
            existing_ptr = existing_pointers.get(kind)
            if isinstance(existing_ptr, str):
                resolved_existing = _resolve_template_path(workspace, Path.home(), existing_ptr)
                if resolved_existing is not None and resolved_existing.is_file():
                    chosen_file = resolved_existing
                    chosen_pointer = existing_ptr

            if chosen_file is None:
                for cand in candidate_names:
                    cand_path = resolved_tpl_dir / cand
                    if cand_path.is_file():
                        chosen_file = cand_path
                        chosen_pointer = f"{rel_prefix}/{cand}"
                        break

            if chosen_file is None or chosen_pointer is None:
                dest_file = resolved_tpl_dir / default_dest_name
                if dest_file.exists() and dest_file.is_symlink():
                    return fail(
                        f"Refusing to write template through symlink {dest_file.as_posix()}.", ErrorCategory.VALIDATION
                    )
                dest_file.write_text(bundled_text, encoding="utf-8", newline="\n")
                chosen_file = dest_file
                chosen_pointer = f"{rel_prefix}/{default_dest_name}"
                seeded.append(chosen_file.as_posix())
            else:
                reused.append(chosen_file.as_posix())

            registered[kind] = chosen_pointer
            active_text = chosen_file.read_text(encoding="utf-8").replace("\r\n", "\n")
            if kind not in baselines:
                baselines[kind] = {
                    "path": chosen_pointer,
                    "plugin_version": self._plugin_version,
                    "bundled_sha256": _sha256_text(bundled_text),
                    "active_sha256": _sha256_text(active_text),
                    "recorded_at": now_iso,
                }

        for aux_asset, aux_candidates, aux_default in _AUXILIARY_ASSETS:
            aux_src = self._assets_dir / aux_asset
            if aux_src.is_file() and not any((resolved_tpl_dir / name).is_file() for name in aux_candidates):
                aux_dest = resolved_tpl_dir / aux_default
                if not aux_dest.is_symlink():
                    aux_dest.write_text(
                        aux_src.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8", newline="\n"
                    )
                    seeded.append(aux_dest.as_posix())

        updates_doc: dict[str, JsonValue] = {
            **existing_updates,
            "schema_version": 1,
            "policies": policies,
            "baselines": baselines,
        }
        write_updates = _write_json_file(updates_path, updates_doc, private=False)
        if not write_updates.ok:
            return fail(write_updates.message, write_updates.category)

        return ok((registered, seeded, reused, updates_path))
