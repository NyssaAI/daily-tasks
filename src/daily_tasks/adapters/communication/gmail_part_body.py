# Responsibility: Validate the body of one Gmail message part.
# Public interface:
# `-- GmailPartBody
#     +-- attachmentId
#     +-- data
#     `-- size
"""Gmail `MessagePartBody` wire shape; `data` is base64url-encoded."""

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class GmailPartBody:
    """Inline body data, or an `attachmentId` when the content must be fetched separately."""

    size: int = 0
    data: str | None = None
    attachmentId: str | None = None  # noqa: N815 - Gmail wire field name
