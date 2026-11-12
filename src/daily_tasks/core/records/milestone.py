"""Responsibility: Represent an immutable Milestone DTO.
Public interface:
`-- Milestone
    +-- assignee
    +-- blocked_by
    +-- created_at
    +-- definition_of_done
    +-- id
    +-- number
    +-- owner
    +-- path
    +-- project_id
    +-- record_version
    +-- resolved_at
    +-- source
    +-- started_at
    +-- state
    +-- tags
    +-- target_date
    +-- task_ids
    +-- title
    +-- type
    `-- updated_at

Milestone DTO.
"""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dod_item import DodItem
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.utc_timestamp import UtcTimestamp
from daily_tasks.core.records.work_state import WorkState


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Milestone:
    """Milestone record with its Definition of Done and task ids."""

    id: UUID7
    type: Literal["milestone"]
    record_version: int
    project_id: UUID7
    number: int
    title: str
    owner: str
    assignee: str | None
    state: WorkState
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    started_at: UtcTimestamp | None
    resolved_at: UtcTimestamp | None
    target_date: date | None
    tags: tuple[str, ...]
    path: str
    definition_of_done: tuple[DodItem, ...]
    task_ids: tuple[UUID7, ...]
    blocked_by: tuple[UUID7, ...]
    source: str
