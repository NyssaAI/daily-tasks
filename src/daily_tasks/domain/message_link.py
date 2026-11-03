# Responsibility: Represent an immutable MessageLink DTO.
# Public interface:
# `-- MessageLink
#     +-- matched_text
#     +-- reasons
#     +-- record_id
#     `-- record_type
"""MessageLink DTO."""

from pydantic import UUID7
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageLink:
    """Pre-matched link from a message to a record, with the matching reasons."""

    record_type: str
    record_id: UUID7
    reasons: tuple[str, ...]
    matched_text: str

