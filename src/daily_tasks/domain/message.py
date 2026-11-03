# Responsibility: Represent an immutable Message DTO.
# Public interface:
# `-- Message
#     +-- attachments
#     +-- body
#     +-- body_format
#     +-- cc
#     +-- channel
#     +-- external_id
#     +-- fetched_at
#     +-- id
#     +-- received_at
#     +-- sender
#     +-- snippet
#     +-- source
#     +-- subject
#     +-- thread_id
#     +-- to
#     `-- url
"""Message DTO."""

from pydantic import Field
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.attachment import Attachment
from daily_tasks.domain.message_address import MessageAddress


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Message:
    """Fetched message (`<messages_root>/YYYY-MM-DD/<source>/<id>/message.json`)."""

    id: str
    source: str
    external_id: str
    thread_id: str
    received_at: UtcTimestamp
    sender: MessageAddress = Field(alias="from")
    to: tuple[MessageAddress, ...]
    cc: tuple[MessageAddress, ...]
    channel: str | None
    subject: str | None
    snippet: str
    body: str
    body_format: str
    attachments: tuple[Attachment, ...]
    url: str | None
    fetched_at: UtcTimestamp

