# Responsibility: Group the state graph derived-facts DTOs.
# Public interface:
# +-- BlockerFacts
# |   +-- owner
# |   +-- planned_for
# |   `-- state
# +-- DodProgress
# |   +-- done
# |   `-- total
# +-- DroppedTask
# |   +-- reason
# |   `-- task_id
# +-- MilestoneFacts
# |   +-- closable
# |   +-- in_progress_plannable
# |   +-- lowest_incomplete
# |   +-- tasks_open
# |   `-- tasks_total
# +-- Rollover
# |   +-- carried
# |   +-- dropped
# |   +-- from_date
# |   `-- status
# +-- StateGraphDerived
# |   +-- blockers
# |   +-- milestones
# |   +-- rollover
# |   +-- summary
# |   +-- tasks
# |   `-- today
# +-- StateGraphSummary
# |   +-- blocked_tasks
# |   +-- carried_forward
# |   +-- changed_outside_app
# |   +-- late_tasks
# |   +-- open_blockers
# |   +-- open_milestones
# |   +-- open_projects
# |   +-- open_tasks
# |   +-- pending_operations
# |   +-- selected_today
# |   `-- unreviewed_messages
# +-- TaskFacts
# |   +-- blocked
# |   +-- carried_from
# |   +-- closable
# |   +-- dod
# |   +-- effective_assignee
# |   +-- eligible
# |   +-- ineligible_reason
# |   +-- late
# |   +-- planned_for
# |   +-- responsibility
# |   `-- waiting_on
# +-- Today
# |   +-- available
# |   +-- future
# |   `-- selected
# `-- TodaySelection
#     +-- delegated
#     +-- follow_up
#     `-- mine
"""Computed facts per task, blocker and milestone, plus rollover, today and summary."""

from collections.abc import Mapping
from datetime import date

from pydantic import MISSING, UUID7, Field
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import PlanItem


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DodProgress:
    """Checked and total Definition of Done items."""

    done: int
    total: int


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TaskFacts:
    """Computed responsibility, eligibility and planning facts for a task."""

    effective_assignee: str
    responsibility: str
    eligible: bool
    ineligible_reason: str | None | MISSING = MISSING
    late: bool
    blocked: bool
    waiting_on: tuple[UUID7, ...] | MISSING = MISSING
    planned_for: date | None
    carried_from: date | None
    dod: DodProgress
    closable: bool


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerFacts:
    """Computed planning facts for a blocker."""

    planned_for: date | None
    owner: str
    state: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MilestoneFacts:
    """Computed progress facts for a milestone."""

    lowest_incomplete: bool
    in_progress_plannable: bool | MISSING = MISSING
    tasks_open: int
    tasks_total: int
    closable: bool


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DroppedTask:
    """Task not carried forward, and why."""

    task_id: UUID7
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Rollover:
    """Carry-forward outcome from the previous plan."""

    from_date: date = Field(alias="from")
    status: str
    carried: tuple[UUID7, ...]
    dropped: tuple[DroppedTask, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TodaySelection:
    """Items selected for today by section."""

    mine: tuple[PlanItem, ...]
    delegated: tuple[PlanItem, ...]
    follow_up: tuple[PlanItem, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Today:
    """Today's selection, available items and items planned for later days."""

    selected: TodaySelection
    available: tuple[UUID7, ...]
    future: Mapping[date, tuple[UUID7, ...]]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphSummary:
    """Headline counts across the state graph."""

    open_projects: int
    open_milestones: int
    open_tasks: int
    late_tasks: int
    blocked_tasks: int
    open_blockers: int
    selected_today: int
    carried_forward: int
    pending_operations: int
    unreviewed_messages: int
    changed_outside_app: int


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraphDerived:
    """Computed facts layer of the state graph."""

    tasks: Mapping[UUID7, TaskFacts]
    blockers: Mapping[UUID7, BlockerFacts]
    milestones: Mapping[UUID7, MilestoneFacts]
    rollover: Rollover
    today: Today
    summary: StateGraphSummary
