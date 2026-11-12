"""Responsibility: Show a screen in the session snapshot and number its rows by the screen's numbering rule.
Public interface:
`-- number_screen(session, key, kind, refs, now)

Session-numbered screens share `rows`/`next_row` and keep numbers forever; `confirm` restarts at 1.
"""

import dataclasses
from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Literal

from daily_tasks.core.planning.planning_session import PlanningSession
from daily_tasks.core.planning.row_ref import RowRef
from daily_tasks.core.planning.screen import Screen


def _screen_rows(screen: Screen | None) -> dict[int, RowRef]:
    if screen is None or not isinstance(screen.rows, Mapping):
        return {}
    return dict(screen.rows)


def number_screen(
    session: PlanningSession,
    key: str,
    kind: Literal["plan-the-day", "assign-days", "confirm"],
    refs: Sequence[RowRef],
    now: datetime,
) -> PlanningSession:
    """Make `key` the current screen showing `refs` in order.

    On session-numbered screens, refs already numbered on this screen keep their number, new refs take the
    next free session numbers, and earlier numbers on the screen are kept. The confirm screen renumbers 1..n.
    """
    if kind == "confirm":
        rows = {index: ref for index, ref in enumerate(refs, start=1)}
        screen = Screen(kind=kind, numbering="screen", shown_at=now, rows=rows)
        screens = {**session.screens, key: screen}
        return dataclasses.replace(session, screens=screens, current_screen=key, updated_at=now)

    screen_rows = _screen_rows(session.screens.get(key))
    known = set(screen_rows.values())
    session_rows = dict(session.rows)
    next_row = session.next_row
    for ref in refs:
        if ref in known:
            continue
        screen_rows[next_row] = ref
        session_rows[next_row] = ref
        known.add(ref)
        next_row += 1
    screen = Screen(kind=kind, numbering="session", shown_at=now, rows=screen_rows)
    return dataclasses.replace(
        session,
        rows=session_rows,
        next_row=next_row,
        screens={**session.screens, key: screen},
        current_screen=key,
        updated_at=now,
    )
