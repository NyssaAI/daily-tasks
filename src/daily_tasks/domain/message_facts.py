"""Responsibility: Represent an immutable MessageFacts DTO.
Public interface:
`-- MessageFacts
    +-- carried_from
    +-- latest_in_thread
    +-- linked
    +-- needs_review
    +-- reviewed
    `-- superseded_by

MessageFacts DTO.
"""

from datetime import date

from pydantic import MISSING
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageFacts:
    """Computed review facts for one message."""

    reviewed: bool
    linked: bool
    latest_in_thread: bool
    superseded_by: str | None
    needs_review: bool
    carried_from: date | None | MISSING = MISSING
