"""Responsibility: Represent an immutable AssignToDay operation.
Public interface:
`-- AssignToDay
    +-- item_id
    +-- kind
    +-- local_date
    +-- record_kind
    `-- row
"""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class AssignToDay:
    """Plan a task or blocker for a local day."""

    kind: Literal["assign-to-day"]
    row: int
    record_kind: RecordKind
    item_id: UUID7
    local_date: date
