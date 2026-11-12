"""Responsibility: Route MCP planning tool calls to workspace-bound PlanningTools instances dynamically.
Public interface:
+-- PlanningToolsDispatcher
|   +-- advance_screen(session_id, target_screen)
|   +-- cancel_session(session_id)
|   +-- confirm_plan(session_id, confirmed)
|   +-- execute_operations(session_id, original_words, operations, verdicts)
|   +-- get_fetch_window(sources, workspace_root)
|   +-- get_session_state(session_id)
|   +-- new(overrides, clock, new_id)
|   `-- start_session(date, focus, messages, checked_sources, workspace_root)
`-- tool_dispatch_error(tool, message, category)

Dynamic dispatcher creating or finding `PlanningTools` per workspace without mutating global settings.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Final, final
from uuid import UUID

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.server.markdown_workspace_reader import MarkdownWorkspaceReader
from daily_tasks.server.planning_tools import PlanningTools, ToolBody
from daily_tasks.server.resolve_server_settings import resolve_default_workspace_root, resolve_server_settings
from daily_tasks.server.tool_reply import tool_reply
from daily_tasks.server.types import ServerOverrides
from daily_tasks.storage.cursor_store import CursorStore
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "mcp.dispatch"
_UNKNOWN_SESSION: Final = "unknown_session: {session_id} is not active; start a new session."


def tool_dispatch_error(
    tool: str,
    message: str,
    category: ErrorCategory | str = ErrorCategory.VALIDATION,
) -> ToolBody:
    """Return a structured error tool reply for dispatch or configuration failures."""
    return tool_reply(tool, fail(message, category), None)


@final
class PlanningToolsDispatcher:
    """Dispatches tool calls to per-workspace `PlanningTools` instances without mutating state."""

    def __init__(
        self,
        overrides: ServerOverrides,
        clock: Callable[[], datetime],
        new_id: Callable[[], UUID],
    ) -> None:
        """Store startup overrides and initialize the in-memory session routing table."""
        self._overrides = overrides
        self._clock = clock
        self._new_id = new_id
        self._session_tools: dict[str, PlanningTools] = {}

    def _resolve_workspace_path(self, workspace_root: str | None) -> Result[Path]:
        if workspace_root is not None:
            trimmed = workspace_root.strip()
            if not trimmed:
                return fail("workspace_root must be a non-empty absolute path.", ErrorCategory.VALIDATION)
            candidate = Path(trimmed).expanduser()
            if not candidate.is_absolute():
                return fail("workspace_root must be an absolute path.", ErrorCategory.VALIDATION)
            return ok(candidate)
        if self._overrides.workspace_root is not None:
            return ok(self._overrides.workspace_root)
        if self._overrides.config_dir is not None:
            default_ws = resolve_default_workspace_root(self._overrides.config_dir)
            if not default_ws.ok:
                return fail(default_ws.message, default_ws.category)
            if default_ws.value is not None:
                return ok(default_ws.value)
        return fail(
            "Workspace root is required. Pass workspace_root, run Daily Tasks Setup "
            "(daily_tasks_setup_status / daily_tasks_configure_workspace) to bind defaultWorkspaceRoot, "
            "or launch with --workspace-root.",
            ErrorCategory.VALIDATION,
        )

    def _create_tools(self, workspace_root: str | None) -> Result[PlanningTools]:
        ws_result = self._resolve_workspace_path(workspace_root)
        if not ws_result.ok:
            _LOGGER.warning(
                "workspace root rejected",
                extra={"operation": _OPERATION, "fields": {"reason": ws_result.message}},
            )
            return fail(ws_result.message, ws_result.category)
        settings_result = resolve_server_settings(ws_result.value, self._overrides)
        if not settings_result.ok:
            _LOGGER.warning(
                "server settings resolution failed",
                extra={"operation": _OPERATION, "fields": {"reason": settings_result.message}},
            )
            return fail(settings_result.message, settings_result.category)
        settings = settings_result.value
        _LOGGER.debug(
            "workspace tools resolved",
            extra={"operation": _OPERATION, "fields": {"workspace": settings.workspace_root.name}},
        )
        store = MarkdownFileStore(
            settings.workspace_root,
            self._clock,
            records_root=settings.projects_root,
            daily_plans_root=settings.daily_plans_root,
            state_root=settings.state_root,
        )
        cursors = CursorStore(settings.state_root, settings.workspace_root.as_posix())
        reader = MarkdownWorkspaceReader(settings, cursor_store=cursors)
        return ok(PlanningTools(settings, reader, store, self._clock, self._new_id, cursors))

    async def start_session(
        self,
        date: str | None = None,
        focus: str | None = None,
        messages: Sequence[Mapping[str, JsonValue]] = (),
        checked_sources: Sequence[str] = (),
        workspace_root: str | None = None,
    ) -> ToolBody:
        """Resolve workspace settings, start a session, and bind `session_id` on success."""
        tools_result = self._create_tools(workspace_root)
        if not tools_result.ok:
            return tool_dispatch_error("daily_tasks_start_session", tools_result.message, tools_result.category)
        tools = tools_result.value
        reply = await tools.start_session(date, focus, messages, checked_sources)
        session_id = reply.get("session_id")
        if reply.get("status") == "ok" and isinstance(session_id, str):
            self._session_tools[session_id] = tools
            _LOGGER.debug("session registered", extra={"operation": _OPERATION, "fields": {"session_id": session_id}})
        return reply

    def get_fetch_window(
        self,
        sources: Sequence[str] = ("gmail", "slack"),
        workspace_root: str | None = None,
    ) -> ToolBody:
        """Resolve workspace settings and return fetch windows for `sources`."""
        tools_result = self._create_tools(workspace_root)
        if not tools_result.ok:
            return tool_dispatch_error("daily_tasks_get_fetch_window", tools_result.message, tools_result.category)
        return tools_result.value.get_fetch_window(sources)

    def _require_session(self, tool: str, session_id: str) -> Result[PlanningTools]:
        try:
            UUID(session_id)
        except ValueError:
            _LOGGER.warning("invalid session id", extra={"operation": _OPERATION, "fields": {"tool": tool}})
            return fail(f"invalid_session_id: {session_id} is not a UUID.", ErrorCategory.VALIDATION)
        tools = self._session_tools.get(session_id)
        if tools is None:
            _LOGGER.warning(
                "unknown session requested",
                extra={"operation": _OPERATION, "fields": {"tool": tool, "session_id": session_id}},
            )
            return fail(_UNKNOWN_SESSION.format(session_id=session_id), ErrorCategory.NOT_FOUND)
        return ok(tools)

    def get_session_state(self, session_id: str) -> ToolBody:
        """Return the current screen of `session_id`."""
        resolved = self._require_session("daily_tasks_get_session_state", session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_get_session_state", resolved.message, resolved.category)
        return resolved.value.get_session_state(session_id)

    def execute_operations(
        self,
        session_id: str,
        original_words: str,
        operations: Sequence[Mapping[str, JsonValue]] = (),
        verdicts: Sequence[Mapping[str, JsonValue]] = (),
    ) -> ToolBody:
        """Dispatch staged operations and verdicts to the workspace owning `session_id`."""
        resolved = self._require_session("daily_tasks_execute_operations", session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_execute_operations", resolved.message, resolved.category)
        return resolved.value.execute_operations(session_id, original_words, operations, verdicts)

    def advance_screen(self, session_id: str, target_screen: int) -> ToolBody:
        """Advance `session_id` to `target_screen`."""
        resolved = self._require_session("daily_tasks_advance_screen", session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_advance_screen", resolved.message, resolved.category)
        return resolved.value.advance_screen(session_id, target_screen)

    def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody:
        """Confirm and persist `session_id`, evicting the session only when confirmation succeeds."""
        resolved = self._require_session("daily_tasks_confirm_plan", session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_confirm_plan", resolved.message, resolved.category)
        reply = resolved.value.confirm_plan(session_id, confirmed)
        if reply.get("status") == "ok" and session_id in self._session_tools:
            del self._session_tools[session_id]
            _LOGGER.debug(
                "session confirmed and evicted",
                extra={"operation": _OPERATION, "fields": {"session_id": session_id}},
            )
        return reply

    def cancel_session(self, session_id: str) -> ToolBody:
        """Cancel `session_id`, evicting the session only when cancellation succeeds."""
        resolved = self._require_session("daily_tasks_cancel_session", session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_cancel_session", resolved.message, resolved.category)
        reply = resolved.value.cancel_session(session_id)
        if reply.get("status") == "ok" and session_id in self._session_tools:
            del self._session_tools[session_id]
            _LOGGER.debug(
                "session cancelled and evicted",
                extra={"operation": _OPERATION, "fields": {"session_id": session_id}},
            )
        return reply
