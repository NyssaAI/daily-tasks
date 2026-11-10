"""Responsibility: Represent an immutable DailyPlan DTO.
Public interface:
`-- DailyPlan
    +-- blockers
    +-- content_hash
    +-- created_at
    +-- decisions
    +-- entries
    +-- focus
    +-- id
    +-- local_date
    +-- notes
    +-- path
    +-- removed_item_ids
    +-- source
    +-- summary
    +-- timezone
    +-- type
    `-- updated_at

DailyPlan DTO.
"""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.blocker_ref import BlockerRef
from daily_tasks.domain.daily_plan_entry import DailyPlanEntry
from daily_tasks.domain.daily_plan_summary import DailyPlanSummary
from daily_tasks.domain.decision_ref import DecisionRef
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


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
