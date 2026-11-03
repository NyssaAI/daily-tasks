# Responsibility: Represent an immutable Suggestions DTO.
# Public interface:
# `-- Suggestions
#     +-- kinds
#     +-- no_suggestion_message_ids
#     +-- note
#     +-- suggestions
#     +-- updated_at
#     `-- workspace_root
"""Suggestions DTO."""

from collections.abc import Mapping
from datetime import date
from pydantic import Field, MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.suggestion import Suggestion


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Suggestions:
    """Pending suggestions buffer (`.nyssa-ai/daily-tasks/suggestions.json`)."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    workspace_root: str
    updated_at: UtcTimestamp
    no_suggestion_message_ids: tuple[str, ...]
    suggestions: tuple[Suggestion, ...]
    kinds: Mapping[str, str] | MISSING = Field(default=MISSING, alias="_kinds")

