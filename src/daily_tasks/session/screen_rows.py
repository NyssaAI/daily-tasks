# Responsibility: Read the numbered rows of one screen in ascending number order.
# Public interface:
# `-- screen_rows(session, key)
"""Rows recorded on a screen of the session snapshot; missing screens have no rows."""

from collections.abc import Mapping

from daily_tasks.domain import PlanningSession, RowRef


def screen_rows(session: PlanningSession, key: str) -> tuple[tuple[int, RowRef], ...]:
    """Return `(number, ref)` pairs shown on screen `key`, sorted by number."""
    screen = session.screens.get(key)
    if screen is None or not isinstance(screen.rows, Mapping):
        return ()
    return tuple(sorted(screen.rows.items()))
