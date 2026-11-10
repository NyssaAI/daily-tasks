"""Responsibility: Confirm today's plan and end the session.
Public interface:
`-- confirm_session(state, now)

SCREEN_3 -> CONFIRMED; unanswered suggestions stay pending and are never accepted here.
"""

import dataclasses
from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.session.require_stage import require_stage
from daily_tasks.session.session_stage import SessionStage
from daily_tasks.session.session_state import SessionState


def confirm_session(state: SessionState, now: datetime) -> Result[SessionState]:
    """Stamp `confirmed_at`; the recap stays the current screen. Conflict off SCREEN_3."""
    guard = require_stage(state, {SessionStage.SCREEN_3}, "confirm the plan", "reply 'finish' to see the plan recap")
    if not guard.ok:
        return guard
    session = dataclasses.replace(state.session, confirmed_at=now, updated_at=now)
    return ok(state.with_session(session, SessionStage.CONFIRMED))
