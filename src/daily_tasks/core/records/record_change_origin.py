"""Responsibility: Represent an immutable RecordChangeOrigin DTO.
Public interface:
`-- RecordChangeOrigin
    +-- kind
    `-- suggestion_id

RecordChangeOrigin DTO.
"""

from pydantic import MISSING, UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordChangeOrigin:
    """What authorized the change."""

    kind: str
    suggestion_id: UUID7 | MISSING = MISSING
