"""Responsibility: Represent an immutable PlanItem record.
Public interface:
`-- PlanItem
    +-- item_id
    `-- record_kind
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanItem:
    """Task or blocker selected for a day."""

    record_kind: RecordKind
    item_id: UUID7
