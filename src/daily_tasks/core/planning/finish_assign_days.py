"""Responsibility: Move from the assign-days screens to the confirm screen.
Public interface:
`-- finish_assign_days(state, now)

SCREEN_2 -> SCREEN_3 ("finish", or "yes" on the last project).
"""

from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.core.planning.require_stage import require_stage
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.planning.show_confirm import show_confirm


def finish_assign_days(state: SessionState, now: datetime) -> Result[SessionState]:
    """Show the recap with rows renumbered from 1. Conflict off SCREEN_2."""
    guard = require_stage(state, {SessionStage.SCREEN_2}, "show the plan recap")
    if not guard.ok:
        return guard
    return ok(show_confirm(state, now))
