"""Responsibility: Represent an immutable DailyPlanEntry record.
Public interface:
`-- DailyPlanEntry
    +-- added_at
    +-- carried_from
    +-- item_id
    +-- record_kind
    `-- section
"""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlanEntry:
    """Task or blocker selected for the day, with its section and carry provenance."""

    record_kind: RecordKind
    item_id: UUID7
    section: Literal["my-work", "delegated-work", "follow-up-work"]
    carried_from: date | None
    added_at: UtcTimestamp
