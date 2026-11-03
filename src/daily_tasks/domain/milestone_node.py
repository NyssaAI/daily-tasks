# Responsibility: Represent an immutable MilestoneNode DTO.
# Public interface:
# `-- MilestoneNode
#     +-- number
#     +-- project_id
#     +-- ref
#     +-- state
#     `-- title
"""MilestoneNode DTO."""

from pydantic import Field, MISSING, UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneNode:
    """Milestone fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    project_id: UUID7
    number: int
    title: str
    state: str

