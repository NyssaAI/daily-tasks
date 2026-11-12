"""Responsibility: Represent an immutable RecordOrigin DTO.
Public interface:
`-- RecordOrigin
    +-- decision_id
    +-- origin_kind
    `-- source_label

RecordOrigin DTO.
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordOrigin:
    """How a record came to exist, for records created from a decision."""

    origin_kind: str
    source_label: str
    decision_id: UUID7
