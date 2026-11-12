"""Responsibility: Represent an immutable ForReviewMessage DTO.
Public interface:
`-- ForReviewMessage
    +-- attachments
    +-- earlier_in_thread
    +-- links
    +-- message_id
    +-- received_at
    +-- sender
    +-- snippet
    +-- source
    `-- subject

ForReviewMessage DTO.
"""

from pydantic import Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.message_link import MessageLink
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.spec_ref import SpecRef
from daily_tasks.core.records.utc_timestamp import UtcTimestamp


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class ForReviewMessage:
    """Message handed to the agent for suggestion proposal."""

    message_id: str
    source: str
    sender: str = Field(alias="from")
    subject: str | None
    snippet: str
    received_at: UtcTimestamp
    earlier_in_thread: tuple[str, ...]
    attachments: tuple[str, ...]
    links: SpecRef | tuple[MessageLink, ...]
