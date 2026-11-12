"""Responsibility: Move the assign-days screen to the next project in order.
Public interface:
`-- next_project(state, now)

SCREEN_2 -> SCREEN_2 ("next"); the last project refuses and points at "finish".
"""

from datetime import datetime

from nyssa_ai_result import ErrorCategory, Result, fail, ok

from daily_tasks.core.planning.require_stage import require_stage
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.planning.show_project import show_project


def next_project(state: SessionState, now: datetime) -> Result[SessionState]:
    """Show the project after `current_project_id`. Conflict off SCREEN_2 or on the last project."""
    guard = require_stage(state, {SessionStage.SCREEN_2}, "move to the next project")
    if not guard.ok:
        return guard
    days = state.session.assign_days
    order = days.project_order
    position = order.index(days.current_project_id) if days.current_project_id in order else -1
    if position + 1 >= len(order):
        return fail(
            "No next project; expected next step: reply 'finish' for the plan recap.",
            ErrorCategory.CONFLICT,
        )
    return ok(show_project(state, order[position + 1], now))
