"""Responsibility: Represent the pending Suggestions buffer for a vault.
Public interface:
`-- Suggestions
    +-- kinds
    +-- no_suggestion_message_ids
    +-- note
    +-- suggestions
    +-- updated_at
    `-- vault_root
"""

from collections.abc import Mapping

from pydantic import MISSING, Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.suggestion import Suggestion
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Suggestions:
    """Pending suggestions buffer (`<runtime_root>/suggestions.json`)."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    vault_root: str
    updated_at: UtcTimestamp
    no_suggestion_message_ids: tuple[str, ...]
    suggestions: tuple[Suggestion, ...]
    kinds: Mapping[str, str] | MISSING = Field(default=MISSING, alias="_kinds")
