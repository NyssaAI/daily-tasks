# Responsibility: Represent an immutable Rollover DTO.
# Public interface:
# `-- Rollover
#     +-- carried
#     +-- dropped
#     +-- from_date
#     `-- status
"""Rollover DTO."""

from datetime import date
from pydantic import Field, UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.dropped_task import DroppedTask


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Rollover:
    """Carry-forward outcome from the previous plan."""

    from_date: date = Field(alias="from")
    status: str
    carried: tuple[UUID7, ...]
    dropped: tuple[DroppedTask, ...]

