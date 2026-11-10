"""Responsibility: Represent an immutable AssignToDay DTO.
Public interface:
`-- AssignToDay
    +-- item_id
    +-- item_type
    +-- kind
    +-- local_date
    `-- row

AssignToDay DTO.
"""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.item_type import ItemType


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class AssignToDay:
    """Plan a task or blocker for a local day."""

    kind: Literal["assign-to-day"]
    row: int
    item_type: ItemType
    item_id: UUID7
    local_date: date
