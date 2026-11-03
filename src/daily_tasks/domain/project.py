# Responsibility: Represent an immutable Project DTO.
# Public interface:
# `-- Project
#     +-- assignee
#     +-- blocker_ids
#     +-- created_at
#     +-- description
#     +-- directory_date
#     +-- id
#     +-- milestone_ids
#     +-- owner
#     +-- path
#     +-- resolved_at
#     +-- source
#     +-- started_at
#     +-- state
#     +-- tags
#     +-- target_date
#     +-- title
#     +-- type
#     `-- updated_at
"""Project DTO."""

from datetime import date
from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.work_state import WorkState


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
