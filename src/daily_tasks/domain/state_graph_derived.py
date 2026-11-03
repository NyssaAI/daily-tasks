# Responsibility: Represent an immutable StateGraphDerived DTO.
# Public interface:
# `-- StateGraphDerived
#     +-- blockers
#     +-- milestones
#     +-- rollover
#     +-- summary
#     +-- tasks
#     `-- today
"""StateGraphDerived DTO."""

from collections.abc import Mapping
from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.blocker_facts import BlockerFacts
from daily_tasks.domain.milestone_facts import MilestoneFacts
from daily_tasks.domain.rollover import Rollover
from daily_tasks.domain.state_graph_summary import StateGraphSummary
from daily_tasks.domain.task_facts import TaskFacts
from daily_tasks.domain.today import Today


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphDerived:
    """Computed facts layer of the state graph."""

    tasks: Mapping[UUID7, TaskFacts]
    blockers: Mapping[UUID7, BlockerFacts]
    milestones: Mapping[UUID7, MilestoneFacts]
    rollover: Rollover
    today: Today
    summary: StateGraphSummary

