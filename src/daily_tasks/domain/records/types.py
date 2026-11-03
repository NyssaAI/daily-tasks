# Responsibility: Group the persisted project record DTOs.
# Public interface:
# +-- Blocker
# |   +-- blocks
# |   +-- created_at
# |   +-- id
# |   +-- impact
# |   +-- number
# |   +-- owner
# |   +-- path
# |   +-- project_id
# |   +-- resolved_at
# |   +-- resolved_when
# |   +-- source
# |   +-- state
# |   +-- title
# |   +-- type
# |   `-- updated_at
# +-- BlockerState
# +-- Milestone
# |   +-- assignee
# |   +-- blocked_by
# |   +-- created_at
# |   +-- definition_of_done
# |   +-- id
# |   +-- number
# |   +-- owner
# |   +-- path
# |   +-- project_id
# |   +-- record_version
# |   +-- resolved_at
# |   +-- source
# |   +-- started_at
# |   +-- state
# |   +-- tags
# |   +-- target_date
# |   +-- task_ids
# |   +-- title
# |   +-- type
# |   `-- updated_at
# +-- Project
# |   +-- assignee
# |   +-- blocker_ids
# |   +-- created_at
# |   +-- description
# |   +-- directory_date
# |   +-- id
# |   +-- milestone_ids
# |   +-- owner
# |   +-- path
# |   +-- resolved_at
# |   +-- source
# |   +-- started_at
# |   +-- state
# |   +-- tags
# |   +-- target_date
# |   +-- title
# |   +-- type
# |   `-- updated_at
# +-- Task
# |   +-- assignee
# |   +-- blocked_by
# |   +-- created_at
# |   +-- definition_of_done
# |   +-- depends_on
# |   +-- id
# |   +-- milestone_id
# |   +-- number
# |   +-- owner
# |   +-- path
# |   +-- project_id
# |   +-- record_version
# |   +-- required_by
# |   +-- resolved_at
# |   +-- source
# |   +-- started_at
# |   +-- state
# |   +-- tags
# |   +-- target_date
# |   +-- title
# |   +-- type
# |   `-- updated_at
# `-- WorkState
"""Project, Milestone, Task and Blocker records parsed from Markdown frontmatter."""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import DodItem
from daily_tasks.domain.utc_timestamp import UtcTimestamp

type WorkState = Literal["not-started", "in-progress", "completed", "cancelled"]
type BlockerState = Literal["open", "resolved"]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Project:
    """Project index record (`projects/YYYY.MM.DD-<title>/project-index.md`)."""

    id: UUID7
    type: Literal["project"]
    title: str
    description: str
    directory_date: date
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
    milestone_ids: tuple[UUID7, ...]
    blocker_ids: tuple[UUID7, ...]
    source: str


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


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Blocker:
    """Blocker record with its impact, resolution condition and blocked records."""

    id: UUID7
    type: Literal["blocker"]
    project_id: UUID7
    number: int
    title: str
    impact: str
    resolved_when: str
    owner: str
    state: BlockerState
    created_at: UtcTimestamp
    updated_at: UtcTimestamp
    resolved_at: UtcTimestamp | None
    path: str
    blocks: tuple[UUID7, ...]
    source: str
