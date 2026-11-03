# Responsibility: Represent an immutable DecisionLogEntry DTO.
# Public interface:
# `-- DecisionLogEntry
#     +-- action
#     +-- after
#     +-- before
#     +-- corrects
#     +-- decided_at
#     +-- decided_by
#     +-- decision
#     +-- edits
#     +-- id
#     +-- operation_id
#     +-- origin
#     +-- original_words
#     +-- question
#     +-- record_ids
#     +-- recorded_at
#     +-- session_id
#     +-- time_defaulted
#     `-- verdict
"""DecisionLogEntry DTO."""

from collections.abc import Mapping
from typing import Literal
from pydantic import JsonValue, UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.actor import Actor
from daily_tasks.domain.decision_origin import DecisionOrigin


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DecisionLogEntry:
    """One adjudicated decision with who decided, when, and the resulting change."""

    id: UUID7
    session_id: UUID7
    question: str
    decision: str
    decided_by: Actor
    decided_at: UtcTimestamp
    recorded_at: UtcTimestamp
    time_defaulted: bool
    original_words: str
    origin: DecisionOrigin
    verdict: Literal["accept", "edit", "reject"] | None
    edits: Mapping[str, JsonValue] | None
    action: str
    operation_id: UUID7 | None
    record_ids: tuple[UUID7, ...]
    before: Mapping[str, JsonValue] | None
    after: Mapping[str, JsonValue] | None
    corrects: UUID7 | None

