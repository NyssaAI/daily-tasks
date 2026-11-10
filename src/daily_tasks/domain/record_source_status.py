"""Responsibility: Represent an immutable RecordSourceStatus DTO.
Public interface:
`-- RecordSourceStatus
    +-- error
    +-- name
    +-- port
    +-- record_count
    `-- status

RecordSourceStatus DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordSourceStatus:
    """Outcome of reading one project-plan or daily-plan source."""

    port: str
    name: str
    status: str
    record_count: int
    error: str | None
