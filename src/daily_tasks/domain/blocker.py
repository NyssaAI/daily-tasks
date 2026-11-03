# Responsibility: Represent an immutable Blocker DTO.
# Public interface:
# `-- Blocker
#     +-- blocks
#     +-- created_at
#     +-- id
#     +-- impact
#     +-- number
#     +-- owner
#     +-- path
#     +-- project_id
#     +-- resolved_at
#     +-- resolved_when
#     +-- source
#     +-- state
#     +-- title
#     +-- type
#     `-- updated_at
"""Blocker DTO."""

from typing import Literal

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.blocker_state import BlockerState
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


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
