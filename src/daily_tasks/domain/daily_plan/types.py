# Responsibility: Group the persisted daily plan DTOs.
# Public interface:
# +-- BlockerRef
# |   +-- blocker_id
# |   `-- blocks
# +-- DailyPlan
# |   +-- blockers
# |   +-- content_hash
# |   +-- created_at
# |   +-- decisions
# |   +-- entries
# |   +-- focus
# |   +-- id
# |   +-- local_date
# |   +-- notes
# |   +-- path
# |   +-- removed_item_ids
# |   +-- source
# |   +-- summary
# |   +-- timezone
# |   +-- type
# |   `-- updated_at
# +-- DailyPlanEntry
# |   +-- added_at
# |   +-- carried_from
# |   +-- item_id
# |   +-- item_type
# |   `-- section
# +-- DailyPlanSummary
# |   +-- late_tasks
# |   +-- open_projects
# |   `-- open_tasks
# `-- DecisionRef
#     +-- id
#     +-- question
#     `-- resolution
"""DailyPlan with its entries, blocker references and decision references."""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import ItemType
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlanSummary:
    """Headline counts shown at the top of the daily plan."""

    open_projects: int
    open_tasks: int
    late_tasks: int


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlanEntry:
    """Task or blocker selected for the day, with its section and carry provenance."""

    item_type: ItemType
    item_id: UUID7
    section: Literal["my-work", "delegated-work", "follow-up-work"]
    carried_from: date | None
    added_at: UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerRef:
    """Blocker under active resolution and the records it blocks."""

    blocker_id: UUID7
    blocks: tuple[UUID7, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionRef:
    """Decision taken during the planning session, as listed in the plan."""

    id: UUID7
    question: str
    resolution: str


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlan:
    """Daily plan record (`daily-plans/YYYY.MM.DD-daily-plan.md`)."""

    id: UUID7
    type: Literal["daily-plan"]
    local_date: date
    timezone: str
    path: str
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    content_hash: str
    focus: str | None
    summary: DailyPlanSummary
    entries: tuple[DailyPlanEntry, ...]
    removed_item_ids: tuple[UUID7, ...]
    blockers: tuple[BlockerRef, ...]
    decisions: tuple[DecisionRef, ...]
    notes: tuple[str, ...]
    source: str
