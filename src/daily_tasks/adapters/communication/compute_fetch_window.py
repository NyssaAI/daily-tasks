# Responsibility: Compute one source's fetch window from its saved cursor or the initial lookback.
# Public interface:
# +-- DEFAULT_INITIAL_LOOKBACK_DAYS
# `-- compute_fetch_window(cursors, source, now, initial_lookback_days)
"""A saved cursor always wins; without one the first pull reaches back `initial_lookback_days` from `now`."""

from datetime import datetime, timedelta
from typing import Final

from daily_tasks.adapters.communication.fetch_window import FetchWindow
from daily_tasks.domain import FetchCursors

DEFAULT_INITIAL_LOOKBACK_DAYS: Final = 7


def compute_fetch_window(
    cursors: FetchCursors, source: str, now: datetime, initial_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS
) -> FetchWindow:
    """Return the window for `source`; a non-positive `initial_lookback_days` raises `ValueError`."""
    if initial_lookback_days < 1:
        raise ValueError("initial_lookback_days must be positive")
    previous = cursors.cursors.get(source)
    since = previous.since if previous is not None else now - timedelta(days=initial_lookback_days)
    return FetchWindow(
        source=source,
        has_cursor=previous is not None,
        since=since,
        after_epoch=int(since.timestamp()),
        last_external_id=previous.last_external_id if previous is not None else None,
        initial_lookback_days=initial_lookback_days,
    )
