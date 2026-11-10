"""Responsibility: Represent an immutable TaskNode DTO.
Public interface:
`-- TaskNode
    +-- assignee
    +-- milestone_id
    +-- owner
    +-- ref
    +-- state
    +-- target_date
    `-- title

TaskNode DTO.
"""

from datetime import date

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TaskNode:
    """Task fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    milestone_id: UUID7
    title: str
    state: str
    owner: str
    assignee: str | None
    target_date: date | None
