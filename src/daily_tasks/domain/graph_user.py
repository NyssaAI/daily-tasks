"""Responsibility: Represent an immutable GraphUser DTO.
Public interface:
`-- GraphUser
    +-- email
    `-- name

GraphUser DTO.
"""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class GraphUser:
    """User the graph was built for."""

    name: str
    email: str
