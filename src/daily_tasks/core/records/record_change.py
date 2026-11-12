"""Responsibility: Represent an immutable RecordChange checkpoint record.
Public interface:
`-- RecordChange
    +-- after
    +-- applied_at
    +-- before
    +-- effects
    +-- expected_hash
    +-- id
    +-- operation_id
    +-- origin
    +-- path
    +-- record_id
    +-- record_kind
    `-- status
"""

from collections.abc import Mapping

from pydantic import UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_change_origin import RecordChangeOrigin
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordChange:
    """Write-ahead checkpoint: expected file hash, before and after values, and status."""

    id: UUID7
    operation_id: UUID7
    origin: RecordChangeOrigin
    record_kind: RecordKind
    record_id: UUID7
    path: str
    expected_hash: str
    before: Mapping[str, JsonValue] | None
    after: Mapping[str, JsonValue] | None
    effects: tuple[JsonValue, ...]
    status: str
    applied_at: UtcTimestamp | None
