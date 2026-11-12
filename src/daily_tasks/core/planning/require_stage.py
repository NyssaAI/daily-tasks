"""Responsibility: Refuse a session transition that is not allowed from the current stage.
Public interface:
`-- require_stage(state, allowed, attempted, expected_next)

Stage guard shared by the lifecycle transitions.
"""

from collections.abc import Collection

from nyssa_ai_result import ErrorCategory, Result, fail, ok

from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState

_NEXT_STEP: dict[SessionStage, str] = {
    SessionStage.INIT: "start the session",
    SessionStage.SCREEN_1: "reply 'yes' to review open projects",
    SessionStage.SCREEN_2: "reply 'next' for the next project or 'finish' for the plan recap",
    SessionStage.SCREEN_3: "confirm today's plan or cancel",
    SessionStage.CONFIRMED: "the session is confirmed; start a new one",
    SessionStage.CANCELLED: "the session is cancelled; start a new one",
}


def require_stage(
    state: SessionState, allowed: Collection[SessionStage], attempted: str, expected_next: str | None = None
) -> Result[SessionState]:
    """Return `state` when its stage is in `allowed`, else a Conflict naming the expected next step."""
    if state.stage in allowed:
        return ok(state)
    hint = expected_next if expected_next is not None else _NEXT_STEP[state.stage]
    return fail(
        f"Cannot {attempted} while the session is at {state.stage.value}; expected next step: {hint}.",
        ErrorCategory.CONFLICT,
    )
