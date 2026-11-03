# Responsibility: Represent an immutable PlanNode DTO.
# Public interface:
# `-- PlanNode
#     +-- completed_ids
#     +-- path
#     +-- ref
#     `-- task_ids
"""PlanNode DTO."""

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanNode:
    """Daily plan fields the graph keeps in memory."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    path: str | MISSING = MISSING
    task_ids: tuple[UUID7, ...]
    completed_ids: tuple[UUID7, ...] | MISSING = MISSING
