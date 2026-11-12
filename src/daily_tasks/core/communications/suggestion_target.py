"""Responsibility: Represent the target record of a pending Suggestion.
Public interface:
`-- SuggestionTarget
    +-- expected_updated_at
    +-- record_id
    `-- record_kind
"""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionTarget:
    """Record targeted by a suggestion along with the expected `updated_at` timestamp."""

    record_kind: RecordKind
    record_id: UUID7
    expected_updated_at: UtcTimestamp
