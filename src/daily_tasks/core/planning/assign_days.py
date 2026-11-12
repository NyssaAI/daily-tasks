"""Responsibility: Represent an immutable AssignDays DTO.
Public interface:
`-- AssignDays
    +-- current_project_id
    +-- include_in_progress_milestones
    +-- project_order
    `-- project_order_rule

AssignDays DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class AssignDays:
    """Project order and position for the assign-days screens."""

    project_order: tuple[UUID7, ...]
    project_order_rule: str
    current_project_id: UUID7 | None
    include_in_progress_milestones: bool
