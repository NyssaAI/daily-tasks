# Responsibility: Represent an immutable SuggestionTarget DTO.
# Public interface:
# `-- SuggestionTarget
#     +-- expected_updated_at
#     +-- record_id
#     `-- record_type
"""SuggestionTarget DTO."""

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SuggestionTarget:
    """Record a suggestion changes, with the version it was proposed against."""

    record_type: str
    record_id: UUID7
    expected_updated_at: UtcTimestamp
