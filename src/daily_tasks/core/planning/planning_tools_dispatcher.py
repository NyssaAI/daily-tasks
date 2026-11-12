"""Responsibility: Route planning tool calls to vault-bound PlanningTools instances dynamically.
Public interface:
+-- PlanningToolsDispatcher
|   +-- advance_screen(session_id, target_screen)
|   +-- cancel_session(session_id)
|   +-- confirm_plan(session_id, confirmed)
|   +-- execute_operations(session_id, original_words, operations, verdicts)
|   +-- get_fetch_window(sources, vault_root)
|   +-- get_session_state(session_id)
|   +-- new(resolver, clock, new_id)
|   `-- start_session(date, focus, messages, checked_sources, vault_root)
`-- tool_dispatch_error(tool, message, category)
"""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Final, final
from uuid import UUID

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.core.planning.collaborator_resolver import CollaboratorResolver
from daily_tasks.core.planning.planning_tools import PlanningTools, ToolBody
from daily_tasks.core.planning.tool_reply import tool_reply

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
    """Dispatches tool calls to per-vault `PlanningTools` instances without mutating state."""

    def __init__(
        self,
        resolver: CollaboratorResolver,
        clock: Callable[[], datetime],
        new_id: Callable[[], UUID],
    ) -> None:
        """Store the collaborator resolver and initialize the in-memory session routing table."""
        self._resolver = resolver
        self._clock = clock
        self._new_id = new_id
        self._session_tools: dict[str, PlanningTools] = {}

    def _create_tools(self, vault_root: str | None) -> Result[PlanningTools]:
        resolved = self._resolver.resolve(vault_root)
        if not resolved.ok:
            return fail(resolved.message, resolved.category)
        collaborators = resolved.value
        return ok(
            PlanningTools(
                collaborators.context,
                collaborators.reader,
                collaborators.committer,
                self._clock,
                self._new_id,
                collaborators.cursor_store,
            )
        )

    async def start_session(
        self,
        date: str | None = None,
        focus: str | None = None,
        messages: Sequence[Mapping[str, JsonValue]] = (),
        checked_sources: Sequence[str] = (),
        vault_root: str | None = None,
    ) -> ToolBody:
        """Resolve vault collaborators, start a session, and bind `session_id` on success."""
        tools_result = self._create_tools(vault_root)
        if not tools_result.ok:
            return tool_dispatch_error("daily_tasks_start_session", tools_result.message, tools_result.category)
        tools = tools_result.value
        reply = await tools.start_session(date, focus, messages, checked_sources)
        session_id = reply.get("session_id")
        if reply.get("status") == "ok" and isinstance(session_id, str):
            self._session_tools[session_id] = tools
        return reply

    def get_fetch_window(
        self,
        sources: Sequence[str] = ("gmail", "slack"),
        vault_root: str | None = None,
    ) -> ToolBody:
        """Resolve vault collaborators and return fetch windows for `sources`."""
        tools_result = self._create_tools(vault_root)
        if not tools_result.ok:
            return tool_dispatch_error("daily_tasks_get_fetch_window", tools_result.message, tools_result.category)
        return tools_result.value.get_fetch_window(sources)

    def _require_session(self, session_id: str) -> Result[PlanningTools]:
        try:
            UUID(session_id)
        except ValueError:
            return fail(f"invalid_session_id: {session_id} is not a UUID.", ErrorCategory.VALIDATION)
        tools = self._session_tools.get(session_id)
        if tools is None:
            return fail(_UNKNOWN_SESSION.format(session_id=session_id), ErrorCategory.NOT_FOUND)
        return ok(tools)

    def get_session_state(self, session_id: str) -> ToolBody:
        """Return the current screen of `session_id`."""
        resolved = self._require_session(session_id)
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
        """Dispatch staged operations and verdicts to the vault owning `session_id`."""
        resolved = self._require_session(session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_execute_operations", resolved.message, resolved.category)
        return resolved.value.execute_operations(session_id, original_words, operations, verdicts)

    def advance_screen(self, session_id: str, target_screen: int) -> ToolBody:
        """Advance `session_id` to `target_screen`."""
        resolved = self._require_session(session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_advance_screen", resolved.message, resolved.category)
        return resolved.value.advance_screen(session_id, target_screen)

    def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody:
        """Confirm and persist `session_id`, evicting the session only when confirmation succeeds."""
        resolved = self._require_session(session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_confirm_plan", resolved.message, resolved.category)
        reply = resolved.value.confirm_plan(session_id, confirmed)
        if reply.get("status") == "ok" and session_id in self._session_tools:
            del self._session_tools[session_id]
        return reply

    def cancel_session(self, session_id: str) -> ToolBody:
        """Cancel `session_id`, evicting the session only when cancellation succeeds."""
        resolved = self._require_session(session_id)
        if not resolved.ok:
            return tool_dispatch_error("daily_tasks_cancel_session", resolved.message, resolved.category)
        reply = resolved.value.cancel_session(session_id)
        if reply.get("status") == "ok" and session_id in self._session_tools:
            del self._session_tools[session_id]
        return reply
