"""Responsibility: Fetch from every configured communication source concurrently and merge messages and cursors.
Public interface:
`-- CommunicationMultiplexer
    +-- NAME
    +-- fetch_new_messages(since)
    +-- name
    `-- new(ports, clock)

Composite `CommunicationPort`: one failing source degrades the fetch instead of failing it.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.domain import FetchCursor, FetchCursors, Message
from daily_tasks.ports import CommunicationPort, FetchBatch

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "communication.fetch_new_messages"


@final
class CommunicationMultiplexer:
    """Run each source's `fetch_new_messages` in parallel; each source owns only its own cursor."""

    NAME: ClassVar[str] = "communication"

    def __init__(self, ports: Sequence[CommunicationPort], clock: Callable[[], datetime]) -> None:
        """Borrow `ports`; duplicate source names raise `ValueError` because they would share one cursor."""
        names = [port.name for port in ports]
        if len(set(names)) != len(names):
            raise ValueError(f"communication source names must be unique: {names}")
        self._ports = tuple(ports)
        self._clock = clock

    @property
    def name(self) -> str:
        """Composite name; it owns no cursor of its own."""
        return self.NAME

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Return all sources' new messages sorted by `received_at` and each source's advanced cursor.

        A failing source keeps its previous cursor position, marked `last_status: "error"` with the
        failure message in `last_error` (a source without a previous cursor gets no entry). Fails with
        `Unavailable` only when every configured source failed.
        """
        started = time.monotonic()
        results = await asyncio.gather(*(port.fetch_new_messages(since) for port in self._ports))
        run_at = self._clock()
        cursors = dict(since.cursors)
        messages: list[Message] = []
        failed: list[str] = []
        for port, result in zip(self._ports, results, strict=True):
            if result.ok:
                messages.extend(result.value.messages)
                advanced = result.value.cursors.cursors.get(port.name)
                if advanced is not None:
                    cursors[port.name] = advanced
                continue
            failed.append(port.name)
            degraded: dict[str, object] = {
                "source": port.name,
                "error": result.message,
                "category": str(result.category),
            }
            _LOGGER.warning("communication source degraded", extra={"operation": _OPERATION, "fields": degraded})
            previous = since.cursors.get(port.name)
            if previous is not None:
                cursors[port.name] = FetchCursor(
                    since=previous.since,
                    last_external_id=previous.last_external_id,
                    last_run_at=run_at,
                    last_status="error",
                    last_error=result.message,
                )
        fields: dict[str, object] = {
            "sources": len(self._ports),
            "failed_sources": failed,
            "fetched": len(messages),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        }
        if self._ports and len(failed) == len(self._ports):
            _LOGGER.error("communication fetch failed", extra={"operation": _OPERATION, "fields": fields})
            return fail(f"All communication sources failed: {', '.join(failed)}.", "Unavailable")
        _LOGGER.info("communication fetch completed", extra={"operation": _OPERATION, "fields": fields})
        messages.sort(key=lambda m: (m.received_at, m.id))
        merged = FetchCursors(workspace_root=since.workspace_root, cursors=cursors)
        return ok(FetchBatch(messages=tuple(messages), cursors=merged))
