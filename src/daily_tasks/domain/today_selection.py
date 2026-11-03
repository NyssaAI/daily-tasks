# Responsibility: Represent an immutable TodaySelection DTO.
# Public interface:
# `-- TodaySelection
#     +-- delegated
#     +-- follow_up
#     `-- mine
"""TodaySelection DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.plan_item import PlanItem


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TodaySelection:
    """Items selected for today by section."""

    mine: tuple[PlanItem, ...]
    delegated: tuple[PlanItem, ...]
    follow_up: tuple[PlanItem, ...]

