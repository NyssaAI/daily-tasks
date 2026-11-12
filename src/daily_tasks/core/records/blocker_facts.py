"""Responsibility: Represent an immutable BlockerFacts DTO.
Public interface:
`-- BlockerFacts
    +-- owner
    +-- planned_for
    `-- state

BlockerFacts DTO.
"""

from datetime import date

from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BlockerFacts:
    """Computed planning facts for a blocker."""

    planned_for: date | None
    owner: str
    state: str
