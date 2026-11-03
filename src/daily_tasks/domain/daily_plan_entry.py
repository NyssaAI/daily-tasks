# Responsibility: Represent an immutable DailyPlanEntry DTO.
# Public interface:
# `-- DailyPlanEntry
#     +-- added_at
#     +-- carried_from
#     +-- item_id
#     +-- item_type
#     `-- section
"""DailyPlanEntry DTO."""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.item_type import ItemType
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlanEntry:
    """Task or blocker selected for the day, with its section and carry provenance."""

    item_type: ItemType
    item_id: UUID7
    section: Literal["my-work", "delegated-work", "follow-up-work"]
    carried_from: date | None
    added_at: UtcTimestamp
