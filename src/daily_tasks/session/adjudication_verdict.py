"""Responsibility: Represent the user's explicit answer to one numbered suggestion row.
Public interface:
`-- AdjudicationVerdict
    +-- edits
    +-- original_words
    +-- row
    +-- screen_id
    +-- suggestion_id
    `-- verdict

Explicit verdict on a suggestion; suggestions without a verdict stay pending.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Literal
from uuid import UUID

from pydantic import JsonValue


@dataclass(frozen=True, slots=True, kw_only=True)
class AdjudicationVerdict:
    """`edits` is required for `edit` and must be None for `accept` and `reject`."""

    suggestion_id: UUID
    verdict: Literal["accept", "edit", "reject"]
    screen_id: str
    row: int
    original_words: str
    edits: Mapping[str, JsonValue] | None = None
