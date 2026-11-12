"""Responsibility: Filter host-fetched messages against shared cursors and advance source cursors deterministically.
Public interface:
`-- ingest_harness_messages(messages, since, now, initial_lookback_days, checked_sources)
"""

from collections.abc import Sequence
from datetime import datetime

from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.compute_fetch_window import (
    DEFAULT_INITIAL_LOOKBACK_DAYS,
    compute_fetch_window,
)
from daily_tasks.core.communications.fetch_cursor import FetchCursor
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.fetch_window import FetchWindow
from daily_tasks.core.communications.types import FetchBatch


def ingest_harness_messages(
    messages: Sequence[CommunicationMessage],
    since: FetchCursors,
    now: datetime,
    initial_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS,
    checked_sources: Sequence[str] = (),
) -> FetchBatch:
    """Return new messages (oldest first) with the cursor of every supplied or checked source advanced."""
    sources = sorted({*(m.source for m in messages), *checked_sources})
    accepted: dict[tuple[str, str], CommunicationMessage] = {}
    cursors = dict(since.cursors)
    for source in sources:
        window = compute_fetch_window(since, source, now, initial_lookback_days)
        fresh = sorted(
            (m for m in messages if m.source == source and _is_new(m, window)),
            key=lambda m: (m.received_at, m.external_id),
        )
        for message in fresh:
            accepted.setdefault((source, message.external_id), message)
        cursors[source] = _advanced(window, fresh, now)
    ordered = sorted(accepted.values(), key=lambda m: (m.received_at, m.external_id))
    return FetchBatch(messages=tuple(ordered), cursors=FetchCursors(vault_root=since.vault_root, cursors=cursors))


def _is_new(message: CommunicationMessage, window: FetchWindow) -> bool:
    if message.external_id == window.last_external_id:
        return False
    return message.received_at > window.since if window.has_cursor else message.received_at >= window.since


def _advanced(window: FetchWindow, messages: Sequence[CommunicationMessage], run_at: datetime) -> FetchCursor:
    newest = messages[-1] if messages else None
    return FetchCursor(
        since=newest.received_at if newest is not None else window.since,
        last_external_id=newest.external_id if newest is not None else window.last_external_id,
        last_run_at=run_at,
        last_status="ok",
        last_error=None,
    )
