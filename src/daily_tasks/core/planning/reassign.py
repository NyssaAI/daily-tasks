"""Responsibility: Represent an immutable Reassign operation.
Public interface:
`-- Reassign
    +-- item_id
    +-- kind
    +-- owner
    +-- record_kind
    `-- row
"""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Reassign:
    """Change the owner of a task or blocker."""

    kind: Literal["reassign"]
    row: int
    record_kind: RecordKind
    item_id: UUID7
    owner: str
