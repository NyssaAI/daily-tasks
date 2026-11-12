"""Responsibility: Represent an immutable SetStatus operation.
Public interface:
`-- SetStatus
    +-- activity_at
    +-- child_dispositions
    +-- kind
    +-- label
    +-- record_id
    +-- record_kind
    +-- row
    `-- state
"""

from collections.abc import Mapping
from typing import Literal

from pydantic import MISSING, UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SetStatus:
    """Change the state of a record addressed by row or milestone label."""

    kind: Literal["set-status"]
    row: int | MISSING = MISSING
    label: str | MISSING = MISSING
    record_kind: RecordKind
    record_id: UUID7
    state: str
    activity_at: UtcTimestamp
    child_dispositions: Mapping[UUID7, str] | MISSING = MISSING
