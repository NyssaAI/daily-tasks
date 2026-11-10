"""Responsibility: Commit staged record changes and write the daily plan only after explicit user confirmation.
Public interface:
`-- ConfirmPlan
    +-- confirm(changes, document, confirmed_by_user)
    `-- new(store)

`confirm_plan` service: apply record changes, then write the plan; never commit implicitly.
"""

import logging
import time
from collections.abc import Sequence
from typing import Final, final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.domain import RecordChange
from daily_tasks.ports import LocalFileStore
from daily_tasks.storage.cst import DailyPlanDocument

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "plan.confirm"


@final
class ConfirmPlan:
    """Borrow `store`; one terminal log outcome per confirmation attempt."""

    def __init__(self, store: LocalFileStore) -> None:
        """Keep `store`; nothing is written until `confirm`."""
        self._store = store

    def confirm(
        self, changes: Sequence[RecordChange], document: DailyPlanDocument, confirmed_by_user: bool
    ) -> Result[str]:
        """Apply `changes`, then write `document`; return the written plan path.

        Fails with `not_confirmed` (Forbidden) without writing anything when the user has not
        explicitly confirmed, or with the store's category; when applying fails (e.g. `Conflict`)
        the daily plan is not written.
        """
        started = time.monotonic()
        fields: dict[str, object] = {"changes": len(changes), "local_date": document.plan.local_date.isoformat()}
        if not confirmed_by_user:
            self._finish("plan confirmation refused", "warn", fields, started, "not_confirmed")
            return fail("not_confirmed: the user has not explicitly confirmed the plan.", "Forbidden")
        if changes:
            applied = self._store.apply(changes)
            if not applied.ok:
                self._finish("record changes not applied", "error", fields, started, str(applied.category))
                return fail(f"apply_failed: {applied.message}", applied.category)
        written = self._store.write_daily_plan(document)
        if not written.ok:
            self._finish("daily plan not written", "error", fields, started, str(written.category))
            return fail(f"plan_write_failed: {written.message}", written.category)
        self._finish("plan confirmed", "info", fields, started, None)
        return ok(written.value)

    def _finish(
        self, message: str, level: str, fields: dict[str, object], started: float, category: str | None
    ) -> None:
        outcome = {**fields, "elapsed_ms": round((time.monotonic() - started) * 1000, 3)}
        if category is not None:
            outcome["category"] = category
        if level == "info":
            _LOGGER.info(message, extra={"operation": _OPERATION, "fields": outcome})
        elif level == "warn":
            _LOGGER.warning(message, extra={"operation": _OPERATION, "fields": outcome})
        else:
            _LOGGER.error(message, extra={"operation": _OPERATION, "fields": outcome})
