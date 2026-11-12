"""Responsibility: Fetch from every configured communication client concurrently and merge messages and cursors.
Public interface:
`-- CommunicationMultiplexer
    +-- NAME
    +-- fetch_new_messages(since)
    +-- name
    `-- new(clients, clock)
"""

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.core.communications.communication_client import CommunicationClient
from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.fetch_cursor import FetchCursor
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.types import FetchBatch

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "communication.fetch_new_messages"


@final
class CommunicationMultiplexer:
    """Composite `CommunicationClient` running each configured client concurrently."""

    NAME: ClassVar[str] = "communication"

    def __init__(self, clients: Sequence[CommunicationClient], clock: Callable[[], datetime]) -> None:
        """Borrow `clients`; duplicate source names raise `ValueError` because they would share one cursor."""
        names = [client.name for client in clients]
        if len(set(names)) != len(names):
            raise ValueError(f"communication source names must be unique: {names}")
        self._clients = tuple(clients)
        self._clock = clock

    @property
    def name(self) -> str:
        """Composite name; it owns no cursor of its own."""
        return self.NAME

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Return all clients' new messages sorted by `received_at` and each source's advanced cursor."""
        started = time.monotonic()
        results = await asyncio.gather(*(client.fetch_new_messages(since) for client in self._clients))
        run_at = self._clock()
        cursors = dict(since.cursors)
        messages: list[CommunicationMessage] = []
        failed: list[str] = []
        for client, result in zip(self._clients, results, strict=True):
            if result.ok:
                messages.extend(result.value.messages)
                advanced = result.value.cursors.cursors.get(client.name)
                if advanced is not None:
                    cursors[client.name] = advanced
                continue
            failed.append(client.name)
            degraded: dict[str, object] = {
                "source": client.name,
                "error": result.message,
                "category": str(result.category),
            }
            _LOGGER.warning("communication source degraded", extra={"operation": _OPERATION, "fields": degraded})
            previous = since.cursors.get(client.name)
            if previous is not None:
                cursors[client.name] = FetchCursor(
                    since=previous.since,
                    last_external_id=previous.last_external_id,
                    last_run_at=run_at,
                    last_status="error",
                    last_error=result.message,
                )
        fields: dict[str, object] = {
            "sources": len(self._clients),
            "failed_sources": failed,
            "fetched": len(messages),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        }
        if self._clients and len(failed) == len(self._clients):
            _LOGGER.error("communication fetch failed", extra={"operation": _OPERATION, "fields": fields})
            return fail(f"All communication sources failed: {', '.join(failed)}.", "Unavailable")
        _LOGGER.info("communication fetch completed", extra={"operation": _OPERATION, "fields": fields})
        messages.sort(key=lambda m: (m.received_at, m.id))
        merged = FetchCursors(vault_root=since.vault_root, cursors=cursors)
        return ok(FetchBatch(messages=tuple(messages), cursors=merged))
