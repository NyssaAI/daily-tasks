# Responsibility: Represent an immutable PlanItem DTO.
# Public interface:
# `-- PlanItem
#     +-- item_id
#     `-- item_type
"""PlanItem DTO."""

from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.item_type import ItemType


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanItem:
    """Task or blocker selected for a day."""

    item_type: ItemType
    item_id: UUID7

