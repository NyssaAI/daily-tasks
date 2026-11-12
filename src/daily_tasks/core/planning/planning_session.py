"""Responsibility: Represent an immutable PlanningSession record.
Public interface:
`-- PlanningSession
    +-- assign_days
    +-- background
    +-- confirmed_at
    +-- current_screen
    +-- focus
    +-- id
    +-- inventory_hash
    +-- labels
    +-- local_date
    +-- next_row
    +-- note
    +-- rows
    +-- rules
    +-- screens
    +-- started_at
    +-- suggestions_file
    +-- timezone
    +-- updated_at
    `-- vault_root
"""

from collections.abc import Mapping
from datetime import date

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.planning.assign_days import AssignDays
from daily_tasks.core.planning.background_fetch import BackgroundFetch
from daily_tasks.core.planning.row_ref import RowRef
from daily_tasks.core.planning.screen import Screen
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PlanningSession:
    """Planning session (`<runtime_root>/sessions/YYYY.MM.DD.json`)."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    id: UUID7
    vault_root: str
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
