"""Responsibility: Define the collaborator contract for persisting adjudicated vault record changes and daily plans.
Public interface:
`-- FileStore
    +-- apply(changes)
    `-- write_daily_plan(document)
"""

from collections.abc import Sequence
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.types import DailyPlanDocument


class FileStore(Protocol):
    """Authorized writer of canonical vault records and dated daily plan documents."""

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        """Verify optimistic hashes and atomically apply adjudicated record changes in place."""
        ...

    def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]:
        """Render and atomically write the dated daily plan document, returning its vault-relative path."""
        ...
