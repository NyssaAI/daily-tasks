"""Responsibility: Move from the plan-the-day screen to the first project's assign-days screen.
Public interface:
`-- review_projects(state, now)

SCREEN_1 -> SCREEN_2 ("yes" to *Ready to review your open projects?*); pending suggestions carry over.
"""

from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.session.require_stage import require_stage
from daily_tasks.session.session_stage import SessionStage
from daily_tasks.session.session_state import SessionState
from daily_tasks.session.show_confirm import show_confirm
from daily_tasks.session.show_project import show_project


def review_projects(state: SessionState, now: datetime) -> Result[SessionState]:
    """Show the first project in `project_order`, or the recap when there is none. Conflict off SCREEN_1."""
    guard = require_stage(state, {SessionStage.SCREEN_1}, "review projects")
    if not guard.ok:
        return guard
    order = state.session.assign_days.project_order
    if not order:
        return ok(show_confirm(state, now))
    return ok(show_project(state, order[0], now))
