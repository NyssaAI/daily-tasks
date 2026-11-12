"""Responsibility: Represent an immutable StateGraphDerived DTO.
Public interface:
`-- StateGraphDerived
    +-- blockers
    +-- milestones
    +-- rollover
    +-- summary
    +-- tasks
    `-- today

StateGraphDerived DTO.
"""

from collections.abc import Mapping

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.blocker_facts import BlockerFacts
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.milestone_facts import MilestoneFacts
from daily_tasks.core.records.rollover import Rollover
from daily_tasks.core.records.state_graph_summary import StateGraphSummary
from daily_tasks.core.records.task_facts import TaskFacts
from daily_tasks.core.records.today import Today


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphDerived:
    """Computed facts layer of the state graph."""

    tasks: Mapping[UUID7, TaskFacts]
    blockers: Mapping[UUID7, BlockerFacts]
    milestones: Mapping[UUID7, MilestoneFacts]
    rollover: Rollover
    today: Today
    summary: StateGraphSummary
