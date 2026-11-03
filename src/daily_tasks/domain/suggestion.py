# Responsibility: Represent an immutable Suggestion DTO.
# Public interface:
# `-- Suggestion
#     +-- created_at
#     +-- created_in_session
#     +-- current
#     +-- evidence
#     +-- id
#     +-- kind
#     +-- proposed
#     +-- rationale
#     +-- source_message_ids
#     +-- target
#     `-- validation
"""Suggestion DTO."""

from collections.abc import Mapping
from typing import Literal

from pydantic import UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.suggestion_target import SuggestionTarget
from daily_tasks.domain.suggestion_validation import SuggestionValidation
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Suggestion:
    """Pending suggestion with its evidence, current values and proposed change."""

    id: UUID7
    kind: Literal["new-task", "status", "dod", "blocker"]
    created_at: UtcTimestamp
    created_in_session: UUID7
    source_message_ids: tuple[str, ...]
    evidence: str
    rationale: str
    target: SuggestionTarget | None
    current: Mapping[str, JsonValue] | None
    proposed: Mapping[str, JsonValue]
    validation: SuggestionValidation
