# Responsibility: Represent an immutable ProjectTree DTO.
# Public interface:
# `-- ProjectTree
#     +-- blocker_ids
#     +-- milestones
#     `-- project_id
"""ProjectTree DTO."""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.milestone_tree import MilestoneTree


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ProjectTree:
    """Project with its nested milestones and blockers."""

    project_id: UUID7
    milestones: tuple[MilestoneTree, ...]
    blocker_ids: tuple[UUID7, ...]
