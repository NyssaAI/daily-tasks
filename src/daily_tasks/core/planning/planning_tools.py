"""Responsibility: Run the planning session tools against in-memory sessions and write only after confirmation.
Public interface:
+-- PlanningTools
|   +-- advance_screen(session_id, target_screen)
|   +-- cancel_session(session_id)
|   +-- confirm_plan(session_id, confirmed)
|   +-- execute_operations(session_id, original_words, operations, verdicts)
|   +-- get_fetch_window(sources, vault_root)
|   +-- get_session_state(session_id)
|   +-- new(context, reader, committer, clock, new_id, cursor_store)
|   `-- start_session(date, focus, messages, checked_sources, vault_root)
`-- ToolBody
"""

import dataclasses
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime
from typing import Final, final
from uuid import UUID

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue, TypeAdapter, ValidationError

from daily_tasks.core.communications.cursor_store import CursorStore
from daily_tasks.core.communications.generate_suggestions import generate_suggestions
from daily_tasks.core.communications.match_messages import match_messages
from daily_tasks.core.planning.actor import Actor
from daily_tasks.core.planning.adjudicate_suggestions import adjudicate_suggestions
from daily_tasks.core.planning.apply_operations import apply_operations
from daily_tasks.core.planning.build_daily_plan_document import build_daily_plan_document
from daily_tasks.core.planning.cancel_session import cancel_session
from daily_tasks.core.planning.confirm_session import confirm_session
from daily_tasks.core.planning.finish_assign_days import finish_assign_days
from daily_tasks.core.planning.harness_message_intake import fetch_window_reply, harness_message_intake, saved_cursors
from daily_tasks.core.planning.live_session import LiveSession
from daily_tasks.core.planning.next_project import next_project
from daily_tasks.core.planning.operations import Operations
from daily_tasks.core.planning.parse_verdicts import parse_verdicts
from daily_tasks.core.planning.refresh_today import refresh_today
from daily_tasks.core.planning.render_assign_days import render_assign_days
from daily_tasks.core.planning.render_confirm_plan import render_confirm_plan
from daily_tasks.core.planning.render_plan_the_day import render_plan_the_day
from daily_tasks.core.planning.review_projects import review_projects
from daily_tasks.core.planning.session_committer import SessionCommitter
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.planning.show_confirm import show_confirm
from daily_tasks.core.planning.start_session import start_session
from daily_tasks.core.planning.start_session_reply import start_session_reply
from daily_tasks.core.planning.tool_reply import tool_reply
from daily_tasks.core.planning.types import PlanningContext
from daily_tasks.core.planning.vault_reader import VaultReader

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
    """Borrow every collaborator; sessions live in memory until confirmed or cancelled."""

    def __init__(
        self,
        context: PlanningContext,
        reader: VaultReader,
        committer: SessionCommitter,
        clock: Callable[[], datetime],
        new_id: Callable[[], UUID],
        cursor_store: CursorStore | None = None,
    ) -> None:
        """Keep the collaborators; `clock` returns aware UTC datetimes."""
        self._context = context
        self._reader = reader
        self._committer = committer
        self._clock = clock
        self._new_id = new_id
        self._cursor_store = cursor_store
        self._sessions: dict[UUID, LiveSession] = {}

    async def start_session(
        self,
        date: str | None = None,
        focus: str | None = None,
        messages: Sequence[Mapping[str, JsonValue]] = (),
        checked_sources: Sequence[str] = (),
        vault_root: str | None = None,
    ) -> ToolBody:
        """Read the vault, pre-match unread messages into pending suggestions, and show screen 1."""
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
        days = self._context.initial_lookback_days
        intake = harness_message_intake(messages, checked_sources, read, self._cursor_store, now, days)
        if not intake.ok:
            return tool_reply(tool, intake, None)
        found, cursors, harness = intake.value.messages, intake.value.cursors, intake.value.sources
        session_id = self._new_id()
        matches = match_messages(graph, found, ())
        vault = self._context.vault_root
        drafted = generate_suggestions(graph, matches, session_id, vault, self._clock, self._new_id)
        initial = SessionState.initial(
            state_graph=graph,
            suggestions=drafted.suggestions,
            session_id=session_id,
            vault_root=vault,
            suggestions_file="suggestions.json",
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
            cursors=cursors,
            malformed_files=read.malformed_files,
        )
        message, payload = start_session_reply(read, harness, len(drafted.suggestions))
        return tool_reply(tool, ok(message), started.value, _render(started.value), payload=payload)

    def get_fetch_window(self, sources: Sequence[str] = ("gmail", "slack"), vault_root: str | None = None) -> ToolBody:
        """Return each source's next fetch window from its saved cursor, else the initial lookback; no session."""
        saved = saved_cursors(self._cursor_store, self._context.vault_root)
        return fetch_window_reply(saved, sources, self._clock(), self._context.initial_lookback_days)

    def get_session_state(self, session_id: str) -> ToolBody:
        """Return the current screen without changing the session."""
        tool = "daily_tasks_get_session_state"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        state = live.value.state
        malformed: list[JsonValue] = [
            {"path": m.path, "kind": m.kind, "code": m.code, "message": m.message} for m in live.value.malformed_files
        ]
        payload: ToolBody = {
            "pending_suggestions": len(state.suggestions),
            "staged_changes": len(live.value.changes),
            "malformed_files": malformed,
        }
        return tool_reply(tool, ok(f"Session is at {state.stage.value}."), state, _render(state), payload=payload)

    def execute_operations(
        self,
        session_id: str,
        original_words: str,
        operations: Sequence[Mapping[str, JsonValue]] = (),
        verdicts: Sequence[Mapping[str, JsonValue]] = (),
    ) -> ToolBody:
        """Apply the user's explicit verdicts and operations all-or-nothing and return the refreshed screen."""
        tool = "daily_tasks_execute_operations"
        live = self._live(session_id)
        if not live.ok:
            return tool_reply(tool, live, None)
        current = live.value
        state = current.state
        if state.stage not in _NEXT_TOOL:
            return tool_reply(tool, fail("Session has ended.", ErrorCategory.CONFLICT), state)
        actor = Actor(kind="person", id=self._context.user_email)
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
        """Apply staged changes, write the daily plan, then append decisions and save session state."""
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
            self._context.projects_prefix,
            self._new_id(),
            now,
        )
        written = self._committer.commit(
            current.changes,
            document,
            current.decisions,
            current.suggestions,
            done.value.session,
            current.cursors,
            confirmed,
        )
        if not written.ok:
            return tool_reply(tool, written, current.state)
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
