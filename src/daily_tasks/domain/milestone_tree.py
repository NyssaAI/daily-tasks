# Responsibility: Represent an immutable MilestoneTree DTO.
# Public interface:
# `-- MilestoneTree
#     +-- milestone_id
#     `-- task_ids
"""MilestoneTree DTO."""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneTree:
    """Milestone and its task ids in order."""

    milestone_id: UUID7
    task_ids: tuple[UUID7, ...]
