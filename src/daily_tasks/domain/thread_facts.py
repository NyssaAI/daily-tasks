"""Responsibility: Represent an immutable ThreadFacts DTO.
Public interface:
`-- ThreadFacts
    +-- last_activity
    +-- linked_record_ids
    +-- message_count
    `-- participants

ThreadFacts DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ThreadFacts:
    """Computed facts for one thread."""

    participants: tuple[str, ...]
    last_activity: UtcTimestamp
    message_count: int
    linked_record_ids: tuple[UUID7, ...]
