# Responsibility: Group the transient plan_apply operation request DTOs.
# Public interface:
# +-- AssignToDay
# |   +-- item_id
# |   +-- item_type
# |   +-- kind
# |   +-- local_date
# |   `-- row
# +-- Operation
# +-- Operations
# |   +-- actor
# |   +-- note
# |   +-- operations
# |   +-- original_words
# |   +-- rules
# |   +-- screen_id
# |   `-- session_id
# +-- Reassign
# |   +-- item_id
# |   +-- item_type
# |   +-- kind
# |   +-- owner
# |   `-- row
# +-- SetStatus
# |   +-- activity_at
# |   +-- child_dispositions
# |   +-- kind
# |   +-- label
# |   +-- record_id
# |   +-- record_type
# |   +-- row
# |   `-- state
# `-- Unplan
#     +-- item_id
#     +-- item_type
#     +-- kind
#     `-- row
"""Operations request: a discriminated union of planning operations on numbered rows."""

from collections.abc import Mapping
from datetime import date
from typing import Annotated, Literal

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.types import Actor, ItemType
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class AssignToDay:
    """Plan a task or blocker for a local day."""

    kind: Literal["assign-to-day"]
    row: int
    item_type: ItemType
    item_id: UUID7
    local_date: date


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Unplan:
    """Remove a task or blocker from its planned day."""

    kind: Literal["unplan"]
    row: int
    item_type: ItemType
    item_id: UUID7


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SetStatus:
    """Change the state of a record addressed by row or milestone label."""

    kind: Literal["set-status"]
    row: int | MISSING = MISSING
    label: str | MISSING = MISSING
    record_type: Literal["task", "blocker", "milestone", "project"]
    record_id: UUID7
    state: str
    activity_at: UtcTimestamp
    child_dispositions: Mapping[UUID7, str] | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Reassign:
    """Change the owner of a task or blocker."""

    kind: Literal["reassign"]
    row: int
    item_type: ItemType
    item_id: UUID7
    owner: str


type Operation = Annotated[AssignToDay | Unplan | SetStatus | Reassign, Field(discriminator="kind")]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Operations:
    """Transient request to plan_apply: the user's words and the parsed operations."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    session_id: UUID7
    screen_id: str
    original_words: str
    actor: Actor
    operations: tuple[Operation, ...]
    rules: Mapping[str, JsonValue] | MISSING = Field(default=MISSING, alias="_rules")
