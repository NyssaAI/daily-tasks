"""Responsibility: Represent a correlated link from an inbound message to a work record.
Public interface:
`-- MessageLink
    +-- matched_text
    +-- reasons
    +-- record_id
    `-- record_kind
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLink:
    """Pre-matched link from a message to a work record with deterministic matching reasons."""

    record_kind: RecordKind
    record_id: UUID7
    reasons: tuple[str, ...]
    matched_text: str
