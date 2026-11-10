"""Responsibility: Represent an immutable Unplan DTO.
Public interface:
`-- Unplan
    +-- item_id
    +-- item_type
    +-- kind
    `-- row

Unplan DTO.
"""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.item_type import ItemType


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Unplan:
    """Remove a task or blocker from its planned day."""

    kind: Literal["unplan"]
    row: int
    item_type: ItemType
    item_id: UUID7
