# Responsibility: Represent an immutable Attachment DTO.
# Public interface:
# `-- Attachment
#     +-- downloaded_at
#     +-- filename
#     +-- id
#     +-- mime_type
#     +-- path
#     +-- sha256
#     +-- size_bytes
#     `-- status
"""Attachment DTO."""

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Attachment:
    """Message attachment and its download outcome."""

    id: str
    filename: str
    mime_type: str
    size_bytes: int
    sha256: str | None
    path: str | None
    downloaded_at: UtcTimestamp | None
    status: str
