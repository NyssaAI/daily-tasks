# Responsibility: Cancel a planning session that has not ended.
# Public interface:
# `-- cancel_session(state, now)
"""Any non-terminal stage -> CANCELLED; pending suggestions stay pending."""

import dataclasses
from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.session.require_stage import require_stage
from daily_tasks.session.session_stage import SessionStage
from daily_tasks.session.session_state import SessionState

_CANCELLABLE = {SessionStage.INIT, SessionStage.SCREEN_1, SessionStage.SCREEN_2, SessionStage.SCREEN_3}


def cancel_session(state: SessionState, now: datetime) -> Result[SessionState]:
    """End the session without writing a plan. Conflict when already confirmed or cancelled."""
    guard = require_stage(state, _CANCELLABLE, "cancel the session")
    if not guard.ok:
        return guard
    session = dataclasses.replace(state.session, updated_at=now)
    return ok(state.with_session(session, SessionStage.CANCELLED))
