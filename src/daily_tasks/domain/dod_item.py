"""Responsibility: Represent an immutable DodItem DTO.
Public interface:
`-- DodItem
    +-- done
    +-- id
    `-- text

DodItem DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DodItem:
    """Definition of Done checklist item with a stable id."""

    id: UUID7
    text: str
    done: bool
