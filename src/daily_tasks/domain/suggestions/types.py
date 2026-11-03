# Responsibility: Group the pending suggestions buffer DTOs.
# Public interface:
# +-- Suggestion
# |   +-- created_at
# |   +-- created_in_session
# |   +-- current
# |   +-- evidence
# |   +-- id
# |   +-- kind
# |   +-- proposed
# |   +-- rationale
# |   +-- source_message_ids
# |   +-- target
# |   `-- validation
# +-- SuggestionTarget
# |   +-- expected_updated_at
# |   +-- record_id
# |   `-- record_type
# +-- SuggestionValidation
# |   +-- issues
# |   `-- ok
# `-- Suggestions
#     +-- kinds
#     +-- no_suggestion_message_ids
#     +-- note
#     +-- suggestions
#     +-- updated_at
#     `-- workspace_root
"""Suggestions proposed from messages and awaiting explicit adjudication."""

from collections.abc import Mapping
from typing import Literal

from pydantic import MISSING, UUID7, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionTarget:
    """Record a suggestion changes, with the version it was proposed against."""

    record_type: str
    record_id: UUID7
    expected_updated_at: UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionValidation:
    """Deterministic validation outcome of a suggestion."""

    ok: bool
    issues: tuple[str, ...]


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


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Suggestions:
    """Pending suggestions buffer (`.nyssa-ai/daily-tasks/suggestions.json`)."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    workspace_root: str
    updated_at: UtcTimestamp
    no_suggestion_message_ids: tuple[str, ...]
    suggestions: tuple[Suggestion, ...]
    kinds: Mapping[str, str] | MISSING = Field(default=MISSING, alias="_kinds")
