"""Responsibility: Validate host-fetched messages and merge them into a session's messages and cursors.
Public interface:
+-- fetch_window_reply(cursors, sources, now, initial_lookback_days)
+-- harness_message_intake(raw_messages, checked_sources, snapshot, cursor_store, now, initial_lookback_days)
`-- saved_cursors(cursor_store, workspace_root)

Messages an assistant harness connection read go through `ingest_harness_messages` like connector reads.
"""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue, TypeAdapter, ValidationError

from daily_tasks.adapters.communication.compute_fetch_window import compute_fetch_window
from daily_tasks.adapters.communication.ingest_harness_messages import ingest_harness_messages
from daily_tasks.domain import FetchCursors, Message
from daily_tasks.server.types import HarnessIntake, WorkspaceSnapshot
from daily_tasks.storage.cursor_store import CursorStore

_TOOL: Final = "daily_tasks_get_fetch_window"
_MESSAGES: Final[TypeAdapter[tuple[Message, ...]]] = TypeAdapter(tuple[Message, ...])


def harness_message_intake(
    raw_messages: Sequence[Mapping[str, JsonValue]],
    checked_sources: Sequence[str],
    snapshot: WorkspaceSnapshot,
    cursor_store: CursorStore | None,
    now: datetime,
    initial_lookback_days: int,
) -> Result[HarnessIntake]:
    """Validate `raw_messages` (`docs/specs/message.json`), keep the new ones and advance their source cursors.

    Harness sources start from the snapshot's advanced cursors, else the saved ones. Without harness input the
    snapshot's messages and cursors pass through. Fails with `Validation` when a message object is malformed,
    or with the cursor store's failure when saved cursors cannot be loaded.
    """
    if not raw_messages and not checked_sources:
        return ok(HarnessIntake(messages=snapshot.messages, cursors=snapshot.cursors, sources=()))
    try:
        messages = _MESSAGES.validate_python(list(raw_messages))
    except ValidationError as error:
        return fail(f"invalid_messages: {error.error_count()} validation errors.", ErrorCategory.VALIDATION)
    workspace = snapshot.graph.context.workspace_root
    base = ok(snapshot.cursors) if snapshot.cursors is not None else saved_cursors(cursor_store, workspace)
    if not base.ok:
        return fail(base.message, base.category)
    batch = ingest_harness_messages(messages, base.value, now, initial_lookback_days, checked_sources)
    known = {(m.source, m.external_id) for m in snapshot.messages}
    fresh = tuple(m for m in batch.messages if (m.source, m.external_id) not in known)
    sources = tuple(sorted({*(m.source for m in messages), *checked_sources}))
    return ok(HarnessIntake(messages=(*snapshot.messages, *fresh), cursors=batch.cursors, sources=sources))


def saved_cursors(cursor_store: CursorStore | None, workspace_root: str) -> Result[FetchCursors]:
    """Load the saved cursors, or empty cursors when no `CursorStore` is configured."""
    if cursor_store is None:
        return ok(FetchCursors(workspace_root=workspace_root, cursors={}))
    return cursor_store.load()


def fetch_window_reply(
    cursors: Result[FetchCursors], sources: Sequence[str], now: datetime, initial_lookback_days: int
) -> dict[str, JsonValue]:
    """Return the sessionless `daily_tasks_get_fetch_window` body: per-source windows, or the load error.

    The `ok` payload is `{"fetch_windows": [...], "initial_lookback_days": n}` with ISO-8601 UTC `since`.
    """
    if not cursors.ok:
        error: dict[str, JsonValue] = {"tool": _TOOL, "status": "error", "session_id": None, "screen_id": None}
        return {**error, "stage": None, "message": cursors.message, "code": str(cursors.category), "payload": None}
    windows: list[JsonValue] = []
    for source in sources:
        window = compute_fetch_window(cursors.value, source, now, initial_lookback_days)
        windows.append(
            {
                "source": window.source,
                "has_cursor": window.has_cursor,
                "since": window.since.isoformat().replace("+00:00", "Z"),
                "after_epoch": window.after_epoch,
                "last_external_id": window.last_external_id,
                "initial_lookback_days": window.initial_lookback_days,
            }
        )
    payload: dict[str, JsonValue] = {"fetch_windows": windows, "initial_lookback_days": initial_lookback_days}
    message = f"Fetch windows for {len(windows)} sources."
    return {"tool": _TOOL, "status": "ok", "message": message, "payload": payload}
