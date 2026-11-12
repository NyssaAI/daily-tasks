"""Responsibility: Prove host-fetched messages follow the same fetch window and cursor rules as communication clients.
Public interface:
+-- NOW
+-- SINCE
+-- test_compute_fetch_window_custom_lookback_bounds_first_pull()
+-- test_compute_fetch_window_non_positive_lookback_raises()
+-- test_compute_fetch_window_saved_cursor_overrides_lookback()
+-- test_compute_fetch_window_without_cursor_defaults_to_7_days()
+-- test_ingest_harness_messages_checked_source_without_messages_records_window_start()
+-- test_ingest_harness_messages_first_pull_keeps_lookback_boundary_and_drops_older()
+-- test_ingest_harness_messages_leaves_unnamed_source_cursors_unchanged()
`-- test_ingest_harness_messages_with_cursor_drops_watermark_and_last_external_id()

`compute_fetch_window` and `ingest_harness_messages` with first-pull lookback and saved-cursor watermarks.
"""

from datetime import UTC, datetime, timedelta

import pytest
from pydantic import TypeAdapter

from daily_tasks.core.communications import (
    CommunicationMessage,
    FetchCursor,
    FetchCursors,
    compute_fetch_window,
    ingest_harness_messages,
)

NOW = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)
SINCE = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)


def _message(external_id: str, received_at: datetime, source: str = "gmail") -> CommunicationMessage:
    return TypeAdapter(CommunicationMessage).validate_python(
        {
            "id": f"{source}:{external_id}",
            "source": source,
            "external_id": external_id,
            "thread_id": f"{source}-thread:{external_id}",
            "received_at": received_at,
            "from": {"name": "Sarah", "address": "sarah@example.com"},
            "to": [],
            "cc": [],
            "channel": None,
            "subject": "Status",
            "snippet": "update",
            "body": "update",
            "body_format": "text",
            "attachments": [],
            "url": None,
            "fetched_at": NOW,
        }
    )


def _cursors(**cursors: FetchCursor) -> FetchCursors:
    return FetchCursors(vault_root="/vault", cursors=cursors)


def _cursor(since: datetime, last_external_id: str | None = None) -> FetchCursor:
    return FetchCursor(
        since=since, last_external_id=last_external_id, last_run_at=since, last_status="ok", last_error=None
    )


def test_compute_fetch_window_without_cursor_defaults_to_7_days() -> None:
    window = compute_fetch_window(_cursors(), "gmail", NOW)

    assert (window.has_cursor, window.since, window.last_external_id) == (False, NOW - timedelta(days=7), None)
    assert (window.after_epoch, window.initial_lookback_days) == (int((NOW - timedelta(days=7)).timestamp()), 7)


def test_compute_fetch_window_custom_lookback_bounds_first_pull() -> None:
    window = compute_fetch_window(_cursors(), "slack", NOW, initial_lookback_days=3)

    assert (window.since, window.initial_lookback_days) == (NOW - timedelta(days=3), 3)


def test_compute_fetch_window_saved_cursor_overrides_lookback() -> None:
    window = compute_fetch_window(_cursors(gmail=_cursor(SINCE, "m0")), "gmail", NOW, initial_lookback_days=3)

    assert (window.has_cursor, window.since, window.last_external_id) == (True, SINCE, "m0")


def test_compute_fetch_window_non_positive_lookback_raises() -> None:
    with pytest.raises(ValueError):
        compute_fetch_window(_cursors(), "gmail", NOW, initial_lookback_days=0)


def test_ingest_harness_messages_first_pull_keeps_lookback_boundary_and_drops_older() -> None:
    cutoff = NOW - timedelta(days=7)
    messages = [_message("old", cutoff - timedelta(seconds=1)), _message("edge", cutoff), _message("new", SINCE)]

    batch = ingest_harness_messages(messages, _cursors(), NOW)

    assert [m.external_id for m in batch.messages] == ["edge", "new"]
    gmail = batch.cursors.cursors["gmail"]
    assert (gmail.since, gmail.last_external_id, gmail.last_run_at, gmail.last_status) == (SINCE, "new", NOW, "ok")


def test_ingest_harness_messages_with_cursor_drops_watermark_and_last_external_id() -> None:
    messages = [
        _message("m0", SINCE + timedelta(minutes=5)),
        _message("at", SINCE),
        _message("m2", SINCE + timedelta(minutes=10)),
        _message("m1", SINCE + timedelta(minutes=1)),
        _message("m1", SINCE + timedelta(minutes=1)),
    ]

    batch = ingest_harness_messages(messages, _cursors(gmail=_cursor(SINCE, "m0")), NOW)

    assert [m.external_id for m in batch.messages] == ["m1", "m2"]
    assert batch.cursors.cursors["gmail"].last_external_id == "m2"


def test_ingest_harness_messages_checked_source_without_messages_records_window_start() -> None:
    previous = _cursor(SINCE, "s0")

    batch = ingest_harness_messages([], _cursors(slack=previous), NOW, checked_sources=["slack", "outlook"])

    slack, outlook = batch.cursors.cursors["slack"], batch.cursors.cursors["outlook"]
    assert (slack.since, slack.last_external_id, slack.last_run_at) == (SINCE, "s0", NOW)
    assert (outlook.since, outlook.last_external_id) == (NOW - timedelta(days=7), None)


def test_ingest_harness_messages_leaves_unnamed_source_cursors_unchanged() -> None:
    gmail = _cursor(SINCE, "g1")

    batch = ingest_harness_messages([_message("s1", SINCE, source="slack")], _cursors(gmail=gmail), NOW)

    assert batch.cursors.cursors["gmail"] == gmail
    assert batch.cursors.vault_root == "/vault"
