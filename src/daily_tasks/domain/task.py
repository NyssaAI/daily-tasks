# Responsibility: Represent an immutable Task DTO.
# Public interface:
# `-- Task
#     +-- assignee
#     +-- blocked_by
#     +-- created_at
#     +-- definition_of_done
#     +-- depends_on
#     +-- id
#     +-- milestone_id
#     +-- number
#     +-- owner
#     +-- path
#     +-- project_id
#     +-- record_version
#     +-- required_by
#     +-- resolved_at
#     +-- source
#     +-- started_at
#     +-- state
#     +-- tags
#     +-- target_date
#     +-- title
#     +-- type
#     `-- updated_at
"""Task DTO."""

from datetime import date
from typing import Literal
from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.dod_item import DodItem
from daily_tasks.domain.work_state import WorkState


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Task:
    """Task record with its Definition of Done and relations."""

    id: UUID7
    type: Literal["task"]
    record_version: int
    project_id: UUID7
    milestone_id: UUID7
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
    depends_on: tuple[UUID7, ...]
    required_by: tuple[UUID7, ...]
    blocked_by: tuple[UUID7, ...]
    source: str

