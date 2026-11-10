"""Responsibility: Represent an immutable StateGraphRecords DTO.
Public interface:
`-- StateGraphRecords
    +-- blockers
    +-- milestones
    +-- plans
    +-- projects
    `-- tasks

StateGraphRecords DTO.
"""

from collections.abc import Mapping
from datetime import date

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.blocker_node import BlockerNode
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.milestone_node import MilestoneNode
from daily_tasks.domain.plan_node import PlanNode
from daily_tasks.domain.project_node import ProjectNode
from daily_tasks.domain.task_node import TaskNode


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphRecords:
    """Flat records by id, and daily plans by local date."""

    projects: Mapping[UUID7, ProjectNode]
    milestones: Mapping[UUID7, MilestoneNode]
    tasks: Mapping[UUID7, TaskNode]
    blockers: Mapping[UUID7, BlockerNode]
    plans: Mapping[date, PlanNode]
