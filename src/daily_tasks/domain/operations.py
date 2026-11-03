# Responsibility: Represent an immutable Operations DTO.
# Public interface:
# `-- Operations
#     +-- actor
#     +-- note
#     +-- operations
#     +-- original_words
#     +-- rules
#     +-- screen_id
#     `-- session_id
"""Operations DTO."""

from collections.abc import Mapping

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.actor import Actor
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.operation import Operation


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
