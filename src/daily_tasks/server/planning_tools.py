# Responsibility: Run the planning session tools against in-memory sessions and write only after confirmation.
# Public interface:
# +-- PlanningTools
# |   +-- advance_screen(session_id, target_screen)
# |   +-- cancel_session(session_id)
# |   +-- confirm_plan(session_id, confirmed)
# |   +-- execute_operations(session_id, original_words, operations, verdicts)
# |   +-- get_session_state(session_id)
# |   +-- new(settings, reader, store, logger, clock, new_id, cursor_store)
# |   `-- start_session(date, focus)
# `-- ToolBody
"""Application service behind the MCP tools; every result follows `docs/specs/tool-results.json`."""

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Final, final
from uuid import UUID

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue, TypeAdapter, ValidationError

from daily_tasks.domain import Actor, Operations, Suggestions
from daily_tasks.matching import generate_suggestions, match_messages
from daily_tasks.ports import LocalFileStore, PortLogger
from daily_tasks.server.live_session import LiveSession
from daily_tasks.server.tool_reply import tool_reply
from daily_tasks.server.types import ServerSettings
from daily_tasks.server.workspace_reader import WorkspaceReader
from daily_tasks.session import (
    ConfirmPlan,
    DecisionLogger,
    SessionStage,
    SessionState,
    adjudicate_suggestions,
    apply_operations,
    cancel_session,
    confirm_session,
    finish_assign_days,
    next_project,
    render_assign_days,
    render_confirm_plan,
    render_plan_the_day,
    review_projects,
    start_session,
)
from daily_tasks.session.build_daily_plan_document import build_daily_plan_document
from daily_tasks.session.parse_verdicts import parse_verdicts
from daily_tasks.session.refresh_today import refresh_today
from daily_tasks.session.show_confirm import show_confirm
from daily_tasks.storage.cursor_store import CursorStore

type ToolBody = dict[str, JsonValue]

_OPERATIONS: Final[TypeAdapter[Operations]] = TypeAdapter(Operations)
_NEXT_TOOL: Final[Mapping[SessionStage, str]] = {
    SessionStage.SCREEN_1: "daily_tasks_advance_screen",
    SessionStage.SCREEN_2: "daily_tasks_advance_screen",
    SessionStage.SCREEN_3: "daily_tasks_confirm_plan",
}


def _render(state: SessionState) -> str:
    if state.stage is SessionStage.SCREEN_1:
        return render_plan_the_day(state)
    if state.stage is SessionStage.SCREEN_2:
        return render_assign_days(state)
    return render_confirm_plan(state)


@final
class PlanningTools:
    """Borrow every collaborator; sessions live in memory until confirmed or cancelled.

    Nothing is written before `confirm_plan(confirmed=True)`; suggestions are never accepted implicitly.
    """

    def __init__(
        self,
        settings: ServerSettings,
        reader: WorkspaceReader,
        store: LocalFileStore,
        logger: PortLogger,
        clock: Callable[[], datetime],
        new_id: Callable[[], UUID],
        cursor_store: CursorStore | None = None,
    ) -> None:
        """Keep the collaborators; `clock` returns aware UTC datetimes."""
        self._settings = settings
        self._reader = reader
        self._store = store
        self._logger = logger
        self._clock = clock
        self._new_id = new_id
        self._cursor_store = cursor_store
        self._sessions: dict[UUID, LiveSession] = {}

    async def start_session(self, date: str | None = None, focus: str | None = None) -> ToolBody:
        """Read the workspace, pre-match unread messages into pending suggestions and show screen 1."""
        tool = "daily_tasks_start_session"
        now = self._clock()
        snapshot = await self._reader.read(now)
        if not snapshot.ok:
            return tool_reply(tool, snapshot, None)
        read = snapshot.value
        graph = read.graph
        if date is not None and date != graph.context.local_date.isoformat():
            message = f"invalid_date: only today's plan ({graph.context.local_date.isoformat()}) can be planned."
            return tool_reply(tool, fail(message, ErrorCategory.VALIDATION), None)
        session_id = self._new_id()
        matches = match_messages(graph, read.messages, ())
        workspace = self._settings.workspace_root.as_posix()
        drafted = generate_suggestions(graph, matches, session_id, workspace, self._clock, self._new_id)
        initial = SessionState.initial(
            state_graph=graph,
            suggestions=drafted.suggestions,
            session_id=session_id,
            workspace_root=workspace,
            suggestions_file=".nyssa-ai/daily-tasks/suggestions.json",
            focus=focus,
            now=now,
        )
        started = start_session(initial, read.previous_plan, now)
        if not started.ok:
            return tool_reply(tool, started, initial)
        self._sessions[session_id] = LiveSession(
            state=started.value,
            suggestions=drafted,
            decisions=(),
            changes=(),
            blockers=read.blockers,
            existing_plan=read.existing_plan,
            previous_plan=read.previous_plan,
            cursors=read.cursors,
        )
        sources: list[JsonValue] = [{"name": s.name, "status": s.status, "error": s.error} for s in read.sources]
        message = f"Session started with {len(drafted.suggestions)} pending suggestions."
        payload: ToolBody = {"pending_suggestions": len(drafted.suggestions), "message_sources": sources}
        return tool_reply(tool, ok(message), started.value, _render(started.value), payload=payload)

    def get_session_state(self, session_id: str) -> ToolBody:
        """Return the current screen without changing the session."""
        tool = "daily_tasks_get_session_state"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        state = live.value.state
        payload: ToolBody = {"pending_suggestions": len(state.suggestions), "staged_changes": len(live.value.changes)}
        return tool_reply(tool, ok(f"Session is at {state.stage.value}."), state, _render(state), payload=payload)

    def execute_operations(
        self,
        session_id: str,
        original_words: str,
        operations: Sequence[Mapping[str, JsonValue]] = (),
        verdicts: Sequence[Mapping[str, JsonValue]] = (),
    ) -> ToolBody:
        """Apply the user's explicit verdicts and operations all-or-nothing and return the refreshed screen.

        Verdicts name suggestion rows of the current screen (`{"row", "verdict", "edits"?}`); operations follow
        `docs/specs/operations.json`. Decisions and record changes are staged until the plan is confirmed.
        """
        tool = "daily_tasks_execute_operations"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        current = live.value
        state = current.state
        if state.stage not in _NEXT_TOOL:
            return tool_reply(tool, fail("Session has ended.", ErrorCategory.CONFLICT), state)
        actor = Actor(kind="person", id=self._settings.user.email)
        now = self._clock()
        parsed = parse_verdicts(state.session, verdicts, original_words)
        if not parsed.ok:
            return tool_reply(tool, parsed, state)
        judged = adjudicate_suggestions(
            current.suggestions, parsed.value, state.state_graph, actor, state.session.id, now, self._new_id
        )
        if not judged.ok:
            return tool_reply(tool, judged, state)
        graph, decisions, changes = judged.value.graph, list(judged.value.decisions), list(judged.value.changes)
        if operations:
            request = self._operations(state, actor, original_words, operations)
            if not request.ok:
                return tool_reply(tool, request, state)
            applied = apply_operations(graph, request.value, self._new_id, now)
            if not applied.ok:
                return tool_reply(tool, applied, state)
            graph = applied.value.graph
            decisions.extend(applied.value.decisions)
            changes.extend(applied.value.changes)
        graph = refresh_today(graph)
        remaining = judged.value.suggestions
        updated = dataclasses.replace(state, state_graph=graph, suggestions=remaining.suggestions)
        if updated.stage is SessionStage.SCREEN_3:
            updated = show_confirm(updated, now)
        self._sessions[state.session.id] = dataclasses.replace(
            current,
            state=updated,
            suggestions=remaining,
            decisions=(*current.decisions, *decisions),
            changes=(*current.changes, *changes),
        )
        message = f"Recorded {len(decisions)} decisions; {len(changes)} record changes staged until confirmation."
        payload: ToolBody = {"decisions": len(decisions), "staged_changes": len(current.changes) + len(changes)}
        return tool_reply(tool, ok(message), updated, _render(updated), payload=payload)

    def advance_screen(self, session_id: str, target_screen: int) -> ToolBody:
        """Move to screen 2 (first or next project) or screen 3 (recap); moving back is refused."""
        tool = "daily_tasks_advance_screen"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        state = live.value.state
        now = self._clock()
        moved: Result[SessionState]
        if target_screen == 2:
            moved = review_projects(state, now) if state.stage is SessionStage.SCREEN_1 else next_project(state, now)
        elif target_screen == 3 and state.stage is SessionStage.SCREEN_1:
            moved = review_projects(state, now)
            if moved.ok and moved.value.stage is SessionStage.SCREEN_2:
                moved = finish_assign_days(moved.value, now)
        elif target_screen == 3:
            moved = finish_assign_days(state, now)
        else:
            moved = fail(f"Cannot move to screen {target_screen}; screens only move forward.", ErrorCategory.CONFLICT)
        if not moved.ok:
            return tool_reply(tool, moved, state, expected_tool=_NEXT_TOOL.get(state.stage))
        self._sessions[state.session.id] = dataclasses.replace(live.value, state=moved.value)
        message = f"Showing {moved.value.session.current_screen}."
        return tool_reply(tool, ok(message), moved.value, _render(moved.value))

    def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody:
        """Apply staged changes, write the daily plan, then append decisions and save session state.

        Requires the user's explicit confirmation on screen 3; without it nothing is written.
        """
        tool = "daily_tasks_confirm_plan"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        current = live.value
        now = self._clock()
        done = confirm_session(current.state, now)
        if not done.ok:
            return tool_reply(tool, done, current.state, expected_tool=_NEXT_TOOL.get(current.state.stage))
        document = build_daily_plan_document(
            done.value,
            current.decisions,
            current.existing_plan,
            current.blockers,
            self._projects_prefix(),
            self._new_id(),
            now,
        )
        written = ConfirmPlan(self._store, self._logger).confirm(current.changes, document, confirmed)
        if not written.ok:
            return tool_reply(tool, written, current.state)
        followups = self._persist(current, done.value)
        if not followups.ok:
            return tool_reply(tool, followups, done.value)
        del self._sessions[current.state.session.id]
        payload: ToolBody = {"daily_plan": written.value, "applied_changes": len(current.changes)}
        return tool_reply(tool, ok(f"Plan written to {written.value}."), done.value, payload=payload)

    def cancel_session(self, session_id: str) -> ToolBody:
        """Discard the session; no file is written."""
        tool = "daily_tasks_cancel_session"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        cancelled = cancel_session(live.value.state, self._clock())
        if not cancelled.ok:
            return tool_reply(tool, cancelled, live.value.state)
        del self._sessions[live.value.state.session.id]
        return tool_reply(tool, ok("Session cancelled; nothing was written."), cancelled.value)

    def _live(self, session_id: str) -> Result[LiveSession]:
        try:
            key = UUID(session_id)
        except ValueError:
            return fail(f"invalid_session_id: '{session_id}' is not a UUID.", ErrorCategory.VALIDATION)
        live = self._sessions.get(key)
        if live is None:
            return fail(f"unknown_session: {session_id} is not active; start a new session.", ErrorCategory.NOT_FOUND)
        return ok(live)

    def _operations(
        self, state: SessionState, actor: Actor, words: str, operations: Sequence[Mapping[str, JsonValue]]
    ) -> Result[Operations]:
        request = {
            "session_id": str(state.session.id),
            "screen_id": state.session.current_screen,
            "original_words": words,
            "actor": {"kind": actor.kind, "id": actor.id},
            "operations": list(operations),
        }
        try:
            return ok(_OPERATIONS.validate_python(request))
        except ValidationError as error:
            return fail(f"invalid_operations: {error.error_count()} validation errors.", ErrorCategory.VALIDATION)

    def _projects_prefix(self) -> str:
        settings = self._settings
        if settings.projects_root.is_relative_to(settings.workspace_root):
            return settings.projects_root.relative_to(settings.workspace_root).as_posix()
        return ""

    def _persist(self, live: LiveSession, state: SessionState) -> Result[None]:
        appended = DecisionLogger(self._store, self._logger).append(live.decisions)
        if not appended.ok:
            return fail(appended.message, appended.category)
        suggestions: Suggestions = live.suggestions
        steps = [self._store.save_suggestions(suggestions), self._store.save_session(state.session)]
        if self._cursor_store is not None and live.cursors is not None:
            steps.append(self._cursor_store.save(live.cursors))
        failed = next((step for step in steps if not step.ok), None)
        return fail(failed.message, failed.category) if failed is not None and not failed.ok else ok(None)
