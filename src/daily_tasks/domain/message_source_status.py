# Responsibility: Represent an immutable MessageSourceStatus DTO.
# Public interface:
# `-- MessageSourceStatus
#     +-- error
#     +-- fetched
#     +-- name
#     +-- since
#     `-- status
"""MessageSourceStatus DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageSourceStatus:
    """Outcome of scanning one communication source for this graph."""

    name: str
    status: str
    since: UtcTimestamp
    fetched: int
    error: str | None
