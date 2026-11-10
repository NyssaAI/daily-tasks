"""Responsibility: Represent an immutable BackgroundSource DTO.
Public interface:
`-- BackgroundSource
    +-- error
    +-- fetched
    +-- name
    +-- new
    `-- status

BackgroundSource DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class BackgroundSource:
    """Fetch outcome for one communication source."""

    name: str
    status: str
    fetched: int
    new: int
    error: str | None
