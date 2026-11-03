# Responsibility: Carry who decided, when, and how ids are minted for one adjudicated operation.
# Public interface:
# `-- OperationContext
#     +-- actor
#     +-- change_origin
#     +-- edits
#     +-- new_id
#     +-- now
#     +-- operation_id
#     +-- origin
#     +-- original_words
#     +-- session_id
#     `-- verdict
"""Context shared by the decision-log entry and record change one operation produces."""

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from daily_tasks.domain import Actor, DecisionOrigin, RecordChangeOrigin


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationContext:
    """Adjudication facts: `now` is the UTC decision time and `new_id` mints UUIDv7 ids."""

    session_id: UUID
    actor: Actor
    now: datetime
    new_id: Callable[[], UUID]
    operation_id: UUID
    original_words: str
    origin: DecisionOrigin
    change_origin: RecordChangeOrigin
    verdict: Literal["accept", "edit", "reject"] | None = None
    edits: Mapping[str, JsonValue] | None = None
