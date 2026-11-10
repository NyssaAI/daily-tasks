"""Responsibility: Represent an immutable PersonIndex DTO.
Public interface:
`-- PersonIndex
    +-- assigned
    `-- owns

PersonIndex DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PersonIndex:
    """Records a person owns and is assigned."""

    owns: tuple[UUID7, ...]
    assigned: tuple[UUID7, ...]
