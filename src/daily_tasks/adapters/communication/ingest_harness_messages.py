# Responsibility: Filter host-fetched messages against the shared cursors and advance them like a connector.
# Public interface:
# `-- ingest_harness_messages(messages, since, now, initial_lookback_days, checked_sources)
"""Messages read through an assistant harness connection follow the same cursor rules as `GmailConnector`."""

from collections.abc import Sequence
from datetime import datetime

from daily_tasks.adapters.communication.compute_fetch_window import (
    DEFAULT_INITIAL_LOOKBACK_DAYS,
    compute_fetch_window,
)
from daily_tasks.adapters.communication.fetch_window import FetchWindow
from daily_tasks.domain import FetchCursor, FetchCursors, Message
from daily_tasks.ports import FetchBatch


def ingest_harness_messages(
    messages: Sequence[Message],
    since: FetchCursors,
    now: datetime,
    initial_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS,
    checked_sources: Sequence[str] = (),
) -> FetchBatch:
    """Return the new messages, oldest first, with the cursor of every supplied or checked source advanced.

    Per source, a message is dropped when its `external_id` is the cursor's `last_external_id`, when it is at
    or before the cursor (`received_at <= since`), or, on a first pull, before the lookback cutoff. Repeats of
    one `(source, external_id)` are kept once. Cursors of sources not named are carried over unchanged.
    """
    sources = sorted({*(m.source for m in messages), *checked_sources})
    accepted: dict[tuple[str, str], Message] = {}
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
    return FetchBatch(
        messages=tuple(ordered), cursors=FetchCursors(workspace_root=since.workspace_root, cursors=cursors)
    )


def _is_new(message: Message, window: FetchWindow) -> bool:
    if message.external_id == window.last_external_id:
        return False
    return message.received_at > window.since if window.has_cursor else message.received_at >= window.since


def _advanced(window: FetchWindow, messages: Sequence[Message], run_at: datetime) -> FetchCursor:
    newest = messages[-1] if messages else None
    return FetchCursor(
        since=newest.received_at if newest is not None else window.since,
        last_external_id=newest.external_id if newest is not None else window.last_external_id,
        last_run_at=run_at,
        last_status="ok",
        last_error=None,
    )
