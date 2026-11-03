# Responsibility: Append adjudicated decisions to the decision log through the local file store.
# Public interface:
# `-- DecisionLogger
#     +-- append(entries)
#     `-- new(store, logger)
"""Decision-log append service; existing entries are never rewritten."""

import time
from collections.abc import Sequence
from typing import final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.domain import DecisionLogEntry
from daily_tasks.ports import LocalFileStore, PortLogger

_OPERATION = "decisions.append"


@final
class DecisionLogger:
    """Borrow `store` and `logger`; logs one terminal outcome per append with counts only."""

    def __init__(self, store: LocalFileStore, logger: PortLogger) -> None:
        """Keep the collaborators; nothing is written until `append`."""
        self._store = store
        self._logger = logger

    def append(self, entries: Sequence[DecisionLogEntry]) -> Result[int]:
        """Append `entries` atomically and return how many were appended (0 is a no-op).

        Fails with the store's error category; then no entry is appended.
        """
        started = time.monotonic()
        if not entries:
            return ok(0)
        appended = self._store.append_decisions(entries)
        fields: dict[str, object] = {"entries": len(entries), "elapsed_ms": _elapsed_ms(started)}
        if not appended.ok:
            fields["category"] = str(appended.category)
            self._logger.error("decision log append failed", fields=fields, operation=_OPERATION)
            return fail(f"Decision log append failed: {appended.message}", appended.category)
        self._logger.info("decisions appended", fields=fields, operation=_OPERATION)
        return ok(len(entries))


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
