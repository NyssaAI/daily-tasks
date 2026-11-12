"""Responsibility: Represent an immutable Unplan operation.
Public interface:
`-- Unplan
    +-- item_id
    +-- kind
    +-- record_kind
    `-- row
"""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Unplan:
    """Remove a task or blocker from its planned day."""

    kind: Literal["unplan"]
    row: int
    record_kind: RecordKind
    item_id: UUID7
