"""Responsibility: Show the confirm screen with its own row numbers starting at 1.
Public interface:
`-- show_confirm(state, now)

Enter `s3`: numbers from screens 1 and 2 stop resolving while the recap is current.
"""

from datetime import datetime

from daily_tasks.session.confirm_refs import confirm_refs
from daily_tasks.session.number_screen import number_screen
from daily_tasks.session.session_stage import SessionStage
from daily_tasks.session.session_state import SessionState


def show_confirm(state: SessionState, now: datetime) -> SessionState:
    """Return the state at SCREEN_3; the caller has already checked the stage."""
    session = number_screen(state.session, "s3", "confirm", confirm_refs(state.state_graph), now)
    return state.with_session(session, SessionStage.SCREEN_3)
