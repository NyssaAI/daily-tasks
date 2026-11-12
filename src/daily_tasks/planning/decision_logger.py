"""Responsibility: Append adjudicated decisions to the decision log store.
Public interface:
`-- DecisionLogger
    +-- append(entries)
    `-- new(store)
"""

import logging
import time
from collections.abc import Sequence
from typing import Final, final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.planning.decision_log_store_json import DecisionLogStoreJson

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "decisions.append"


@final
class DecisionLogger:
    """Borrow `store`; logs one terminal outcome per append with counts only."""

    def __init__(self, store: DecisionLogStoreJson) -> None:
        """Keep `store`; nothing is written until `append`."""
        self._store = store

    def append(self, entries: Sequence[DecisionLogEntry]) -> Result[int]:
        """Append `entries` atomically and return how many were appended (0 is a no-op)."""
        started = time.monotonic()
        if not entries:
            return ok(0)
        appended = self._store.append_decisions(entries)
        fields: dict[str, object] = {"entries": len(entries), "elapsed_ms": _elapsed_ms(started)}
        if not appended.ok:
            fields["category"] = str(appended.category)
            _LOGGER.error("decision log append failed", extra={"operation": _OPERATION, "fields": fields})
            return fail(f"Decision log append failed: {appended.message}", appended.category)
        _LOGGER.info("decisions appended", extra={"operation": _OPERATION, "fields": fields})
        return ok(len(entries))


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
