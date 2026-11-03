# Responsibility: Validate one message returned by Gmail `users.messages.get`.
# Public interface:
# `-- GmailRawMessage
#     +-- id
#     +-- internalDate
#     +-- payload
#     +-- snippet
#     `-- threadId
"""Gmail `Message` wire shape; fields the connector does not use are ignored."""

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass

from daily_tasks.adapters.communication.gmail_message_part import GmailMessagePart


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class GmailRawMessage:
    """Message as Gmail sends it; `internalDate` is epoch milliseconds as a decimal string."""

    id: str = Field(min_length=1)
    threadId: str = Field(min_length=1)  # noqa: N815 - Gmail wire field name
    internalDate: str = Field(pattern=r"^\d+$")  # noqa: N815 - Gmail wire field name
    snippet: str = ""
    payload: GmailMessagePart | None = None
