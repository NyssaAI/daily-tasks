"""Responsibility: Add newly arrived pending suggestions to a running session without renumbering rows.
Public interface:
`-- add_suggestions(state, suggestions, now)

Late suggestions take the next free session numbers on `s1`; existing numbers never change meaning.
"""

import dataclasses
from collections.abc import Mapping
from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.core.communications.suggestion import Suggestion
from daily_tasks.core.planning.number_screen import number_screen
from daily_tasks.core.planning.require_stage import require_stage
from daily_tasks.core.planning.row_ref import RowRef
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState

_RUNNING = {SessionStage.INIT, SessionStage.SCREEN_1, SessionStage.SCREEN_2, SessionStage.SCREEN_3}


def add_suggestions(state: SessionState, suggestions: tuple[Suggestion, ...], now: datetime) -> Result[SessionState]:
    """Keep the suggestions pending; when `s1` is current, append rows for ids not shown yet.

    Conflict when the session is confirmed or cancelled. Nothing here accepts a suggestion.
    """
    guard = require_stage(state, _RUNNING, "add suggestions")
    if not guard.ok:
        return guard
    known = {suggestion.id for suggestion in state.suggestions}
    merged = (*state.suggestions, *(s for s in suggestions if s.id not in known))
    updated = dataclasses.replace(state, suggestions=merged)
    if state.session.current_screen != "s1":
        return ok(updated)
    shown = state.session.screens["s1"].rows
    existing = tuple(shown.values()) if isinstance(shown, Mapping) else ()
    refs = (*existing, *(RowRef(kind="suggestion", id=s.id) for s in merged))
    session = number_screen(state.session, "s1", "plan-the-day", refs, now)
    return ok(updated.with_session(session, state.stage))
