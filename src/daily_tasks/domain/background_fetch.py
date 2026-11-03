# Responsibility: Represent an immutable BackgroundFetch DTO.
# Public interface:
# `-- BackgroundFetch
#     +-- completed_at
#     +-- sources
#     +-- started_at
#     `-- status
"""BackgroundFetch DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.background_source import BackgroundSource


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BackgroundFetch:
    """Background message fetch started with the session."""

    status: str
    started_at: UtcTimestamp
    completed_at: UtcTimestamp | None
    sources: tuple[BackgroundSource, ...]

