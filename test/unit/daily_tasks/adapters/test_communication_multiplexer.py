"""Responsibility: Prove CommunicationMultiplexer merges sources and degrades gracefully on partial failure.
Public interface:
+-- NOW
+-- T0
+-- test_communication_multiplexer_all_sources_failing_fails_the_fetch(log_capture)
+-- test_communication_multiplexer_duplicate_source_names_are_rejected()
+-- test_communication_multiplexer_merges_messages_sorted_and_cursors_per_source()
+-- test_communication_multiplexer_partial_failure_keeps_previous_cursor_marked_error(log_capture)
`-- test_communication_multiplexer_runs_sources_concurrently()

Composite communication fetch over fake communication ports.
"""

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

import pytest
from nyssa_ai_result import Err, Ok, Result, fail, ok
from pydantic import TypeAdapter

from conftest import LogCapture
from daily_tasks.adapters.communication.communication_multiplexer import CommunicationMultiplexer
from daily_tasks.domain import FetchCursor, FetchCursors, Message, MessageAddress
from daily_tasks.ports import FetchBatch

T0 = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
NOW = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)


def _message(source: str, minutes: int) -> Message:
    return TypeAdapter(Message).validate_python(
        dict(
            id=f"{source}:{minutes}",
            source=source,
            external_id=str(minutes),
            thread_id=f"{source}-thread:{minutes}",
            received_at=T0 + timedelta(minutes=minutes),
            sender=MessageAddress(name=None, address="someone"),
            to=(),
            cc=(),
            channel=None,
            subject=None,
            snippet="",
            body="",
            body_format="text",
            attachments=(),
            url=None,
            fetched_at=NOW,
        )
    )


def _cursor(minutes: int, status: str = "ok", error: str | None = None) -> FetchCursor:
    return FetchCursor(
        since=T0 + timedelta(minutes=minutes),
        last_external_id=str(minutes),
        last_run_at=T0,
        last_status=status,
        last_error=error,
    )


@dataclass
class _FakePort:
    """Returns its messages and advances its own cursor to the newest one, or fails with `error`."""

    source: str
    minutes: tuple[int, ...] = ()
    error: str | None = None
    started: asyncio.Event | None = None

    @property
    def name(self) -> str:
        return self.source

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        await asyncio.sleep(0)
        if self.error is not None:
            return fail(self.error, "Forbidden")
        messages = tuple(_message(self.source, m) for m in self.minutes)
        cursors = dict(since.cursors)
        if self.minutes:
            cursors[self.source] = _cursor(max(self.minutes))
        return ok(
            FetchBatch(messages=messages, cursors=FetchCursors(workspace_root=since.workspace_root, cursors=cursors))
        )


def _since() -> FetchCursors:
    return FetchCursors(workspace_root="/vault", cursors={"gmail": _cursor(0), "slack": _cursor(0)})


def test_communication_multiplexer_merges_messages_sorted_and_cursors_per_source() -> None:
    ports = [_FakePort("gmail", (5, 1)), _FakePort("slack", (3,))]

    result = asyncio.run(CommunicationMultiplexer(ports, lambda: NOW).fetch_new_messages(_since()))

    assert isinstance(result, Ok)
    assert [m.id for m in result.value.messages] == ["gmail:1", "slack:3", "gmail:5"]
    assert result.value.cursors.cursors["gmail"] == _cursor(5)
    assert result.value.cursors.cursors["slack"] == _cursor(3)


def test_communication_multiplexer_partial_failure_keeps_previous_cursor_marked_error(
    log_capture: LogCapture,
) -> None:
    ports = [_FakePort("gmail", (2,)), _FakePort("slack", error="token_revoked")]

    result = asyncio.run(CommunicationMultiplexer(ports, lambda: NOW).fetch_new_messages(_since()))

    assert isinstance(result, Ok)
    assert [m.id for m in result.value.messages] == ["gmail:2"]
    slack = result.value.cursors.cursors["slack"]
    assert (slack.since, slack.last_external_id) == (T0, "0")
    assert (slack.last_status, slack.last_error, slack.last_run_at) == ("error", "token_revoked", NOW)
    assert result.value.cursors.cursors["gmail"] == _cursor(2)
    assert ("warn", "communication source degraded") in [(r[0], r[1]) for r in log_capture.records]
    assert log_capture.records[-1][0] == "info"
    assert log_capture.records[-1][2]["failed_sources"] == ["slack"]


def test_communication_multiplexer_all_sources_failing_fails_the_fetch(log_capture: LogCapture) -> None:
    ports = [_FakePort("gmail", error="invalid_grant"), _FakePort("slack", error="token_revoked")]

    result = asyncio.run(CommunicationMultiplexer(ports, lambda: NOW).fetch_new_messages(_since()))

    assert isinstance(result, Err)
    assert str(result.category) == "Unavailable"
    assert log_capture.records[-1][0] == "error"


def test_communication_multiplexer_runs_sources_concurrently() -> None:
    order: list[str] = []

    @dataclass
    class _Ordered:
        source: str

        @property
        def name(self) -> str:
            return self.source

        async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
            order.append(f"start:{self.source}")
            await asyncio.sleep(0)
            order.append(f"end:{self.source}")
            return ok(FetchBatch(messages=(), cursors=since))

    asyncio.run(CommunicationMultiplexer([_Ordered("a"), _Ordered("b")], lambda: NOW).fetch_new_messages(_since()))

    assert order[:2] == ["start:a", "start:b"]


def test_communication_multiplexer_duplicate_source_names_are_rejected() -> None:
    with pytest.raises(ValueError, match="unique"):
        CommunicationMultiplexer([_FakePort("slack"), _FakePort("slack")], lambda: NOW)
