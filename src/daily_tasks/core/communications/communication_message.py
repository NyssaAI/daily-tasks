"""Responsibility: Represent an immutable CommunicationMessage record.
Public interface:
`-- CommunicationMessage
    +-- attachments
    +-- body
    +-- body_format
    +-- cc
    +-- channel
    +-- external_id
    +-- fetched_at
    +-- id
    +-- received_at
    +-- sender
    +-- snippet
    +-- source
    +-- subject
    +-- thread_id
    +-- to
    `-- url
"""

from pydantic import Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.attachment import Attachment
from daily_tasks.core.communications.message_address import MessageAddress
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class CommunicationMessage:
    """Normalized inbound communication message from email or chat."""

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
