# Responsibility: Validate one (possibly nested) MIME part of a Gmail message.
# Public interface:
# `-- GmailMessagePart
#     +-- body
#     +-- filename
#     +-- headers
#     +-- mimeType
#     `-- parts
"""Gmail `MessagePart` wire shape; multipart messages nest parts recursively."""

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass

from daily_tasks.adapters.communication.gmail_header import GmailHeader
from daily_tasks.adapters.communication.gmail_part_body import GmailPartBody


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class GmailMessagePart:
    """MIME part; the top-level part carries the message headers."""

    mimeType: str = ""  # noqa: N815 - Gmail wire field name
    filename: str = ""
    headers: tuple[GmailHeader, ...] = ()
    body: GmailPartBody | None = None
    parts: tuple["GmailMessagePart", ...] = ()
