# Responsibility: Represent an immutable FetchCursor DTO.
# Public interface:
# `-- FetchCursor
#     +-- last_error
#     +-- last_external_id
#     +-- last_run_at
#     +-- last_status
#     `-- since
"""FetchCursor DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FetchCursor:
    """Fetch position and last outcome for one communication source."""

    since: UtcTimestamp
    last_external_id: str | None
    last_run_at: UtcTimestamp | None
    last_status: str
    last_error: str | None
