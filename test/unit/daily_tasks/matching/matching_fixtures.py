# Responsibility: Build the spec state graph and small messages for the matching tests.
# Public interface:
# +-- BUILT_AT
# +-- message(message_id, body, sender, thread_id, subject, received_at)
# +-- sequential_ids()
# `-- state_graph()
"""Matching fixtures built from the canonical `docs/specs` examples."""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from itertools import count
from typing import Final
from uuid import UUID

from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import Message, StateGraph

BUILT_AT: Final[datetime] = datetime(2026, 11, 3, 14, 5, tzinfo=UTC)
_GRAPH: Final[TypeAdapter[StateGraph]] = TypeAdapter(StateGraph)
_MESSAGE: Final[TypeAdapter[Message]] = TypeAdapter(Message)


def state_graph() -> StateGraph:
    """The spec state graph: tasks such as 'Slack connector' and blockers such as 'Vendor contract signature'."""
    return _GRAPH.validate_python(load_spec("state-graph.json"))


def message(
    message_id: str,
    body: str,
    sender: str = "alex@example.com",
    thread_id: str | None = None,
    subject: str | None = None,
    received_at: str = "2026-11-03T12:00:00Z",
) -> Message:
    """A text message with no attachments; the thread defaults to one per message."""
    return _MESSAGE.validate_python(
        {
            "id": message_id,
            "source": message_id.split(":", 1)[0],
            "external_id": message_id.split(":", 1)[1],
            "thread_id": thread_id or f"thread:{message_id}",
            "received_at": received_at,
            "from": {"name": None, "address": sender},
            "to": [{"name": "Jordan", "address": "jordan@example.com"}],
            "cc": [],
            "channel": None,
            "subject": subject,
            "snippet": body[:80],
            "body": body,
            "body_format": "text",
            "attachments": [],
            "url": None,
            "fetched_at": "2026-11-03T14:00:00Z",
        }
    )


def sequential_ids() -> Callable[[], UUID]:
    """Deterministic UUIDv7 factory: ...-000000000001, ...-000000000002, ..."""
    numbers: Iterator[int] = count(1)
    return lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")
