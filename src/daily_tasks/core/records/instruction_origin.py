"""Responsibility: Represent an immutable InstructionOrigin DTO.
Public interface:
`-- InstructionOrigin
    +-- kind
    +-- row
    `-- screen_id

InstructionOrigin DTO.
"""

from typing import Literal

from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class InstructionOrigin:
    """Decision given as a direct instruction on a numbered row."""

    kind: Literal["instruction"]
    screen_id: str
    row: int
