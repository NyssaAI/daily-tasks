"""Responsibility: Start a planning session by showing the plan-the-day screen.
Public interface:
`-- start_session(state, previous_plan, now)

INIT -> SCREEN_1: number today's tasks, carried-forward tasks and pending suggestions on `s1`.
"""

from datetime import datetime

from nyssa_ai_result import Result, ok

from daily_tasks.core.planning.number_screen import number_screen
from daily_tasks.core.planning.plan_the_day_refs import plan_the_day_refs
from daily_tasks.core.planning.require_stage import require_stage
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.records.daily_plan import DailyPlan


def start_session(state: SessionState, previous_plan: DailyPlan | None, now: datetime) -> Result[SessionState]:
    """Show `s1`; pending suggestions are numbered but stay pending. Conflict unless the stage is INIT."""
    guard = require_stage(state, {SessionStage.INIT}, "start the session")
    if not guard.ok:
        return guard
    refs = plan_the_day_refs(state.state_graph, previous_plan, state.suggestions)
    session = number_screen(state.session, "s1", "plan-the-day", refs, now)
    return ok(state.with_session(session, SessionStage.SCREEN_1))
