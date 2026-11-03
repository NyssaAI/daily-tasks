# Responsibility: Represent an immutable MessageLogEntry DTO.
# Public interface:
# `-- MessageLogEntry
#     +-- day
#     +-- location
#     +-- message_id
#     +-- reviewed
#     `-- reviewed_at
"""MessageLogEntry DTO."""

from datetime import date

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLogEntry:
    """Where a fetched message is stored and whether it was reviewed."""

    day: date
    message_id: str
    location: str
    reviewed: bool
    reviewed_at: UtcTimestamp | None
