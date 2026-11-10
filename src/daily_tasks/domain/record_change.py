"""Responsibility: Represent an immutable RecordChange DTO.
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
    +-- record_type
    `-- status

RecordChange DTO.
"""

from collections.abc import Mapping
from typing import Literal

from pydantic import UUID7, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.record_change_origin import RecordChangeOrigin
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class RecordChange:
    """Write-ahead checkpoint: expected file hash, before and after values, and status."""

    id: UUID7
    operation_id: UUID7
    origin: RecordChangeOrigin
    record_type: Literal["project", "milestone", "task", "blocker", "daily-plan"]
    record_id: UUID7
    path: str
    expected_hash: str
    before: Mapping[str, JsonValue] | None
    after: Mapping[str, JsonValue] | None
    effects: tuple[JsonValue, ...]
    status: str
    applied_at: UtcTimestamp | None
