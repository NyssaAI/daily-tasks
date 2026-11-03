# Responsibility: Group the persisted planning session DTOs.
# Public interface:
# +-- AssignDays
# |   +-- current_project_id
# |   +-- include_in_progress_milestones
# |   +-- project_order
# |   `-- project_order_rule
# +-- BackgroundFetch
# |   +-- completed_at
# |   +-- sources
# |   +-- started_at
# |   `-- status
# +-- BackgroundSource
# |   +-- error
# |   +-- fetched
# |   +-- name
# |   +-- new
# |   `-- status
# +-- PlanningSession
# |   +-- assign_days
# |   +-- background
# |   +-- confirmed_at
# |   +-- current_screen
# |   +-- focus
# |   +-- id
# |   +-- inventory_hash
# |   +-- labels
# |   +-- local_date
# |   +-- next_row
# |   +-- note
# |   +-- rows
# |   +-- rules
# |   +-- screens
# |   +-- started_at
# |   +-- suggestions_file
# |   +-- timezone
# |   +-- updated_at
# |   `-- workspace_root
# +-- RowRef
# |   +-- id
# |   `-- kind
# `-- Screen
#     +-- kind
#     +-- numbering
#     +-- rows
#     `-- shown_at
"""PlanningSession with background fetch status, row maps and screen-scoped numbering."""

from collections.abc import Mapping
from datetime import date
from typing import Literal

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BackgroundSource:
    """Fetch outcome for one communication source."""

    name: str
    status: str
    fetched: int
    new: int
    error: str | None


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BackgroundFetch:
    """Background message fetch started with the session."""

    status: str
    started_at: UtcTimestamp
    completed_at: UtcTimestamp | None
    sources: tuple[BackgroundSource, ...]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class AssignDays:
    """Project order and position for the assign-days screens."""

    project_order: tuple[UUID7, ...]
    project_order_rule: str
    current_project_id: UUID7 | None
    include_in_progress_milestones: bool


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RowRef:
    """Item a numbered row points at."""

    kind: Literal["task", "blocker", "suggestion", "milestone", "project"]
    id: UUID7


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Screen:
    """Screen shown in the session and how its rows are numbered."""

    kind: Literal["plan-the-day", "assign-days", "confirm"]
    numbering: Literal["session", "screen"]
    shown_at: UtcTimestamp | None
    rows: Mapping[int, RowRef] | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanningSession:
    """Planning session (`.nyssa-ai/daily-tasks/sessions/YYYY.MM.DD.json`)."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    id: UUID7
    workspace_root: str
    local_date: date
    timezone: str
    started_at: UtcTimestamp
    updated_at: UtcTimestamp
    confirmed_at: UtcTimestamp | None
    focus: str | None
    inventory_hash: str
    background: BackgroundFetch
    suggestions_file: str
    current_screen: str
    assign_days: AssignDays
    next_row: int
    rows: Mapping[int, RowRef]
    labels: Mapping[UUID7, Mapping[str, UUID7]]
    screens: Mapping[str, Screen]
    rules: Mapping[str, JsonValue] | MISSING = Field(default=MISSING, alias="_rules")
