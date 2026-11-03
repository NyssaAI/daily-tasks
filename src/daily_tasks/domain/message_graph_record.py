# Responsibility: Represent an immutable MessageGraphRecord DTO.
# Public interface:
# `-- MessageGraphRecord
#     +-- attachment_ids
#     +-- channel
#     +-- location
#     +-- received_at
#     +-- ref
#     +-- sender
#     +-- snippet
#     +-- source
#     +-- subject
#     `-- thread_id
"""MessageGraphRecord DTO."""

from pydantic import Field, MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraphRecord:
    """Message summary keyed by message id."""

    ref: str | MISSING = Field(default=MISSING, alias="$ref")
    source: str
    thread_id: str
    received_at: UtcTimestamp
    sender: str = Field(alias="from")
    subject: str | None
    channel: str | None | MISSING = MISSING
    snippet: str
    attachment_ids: tuple[str, ...]
    location: str

