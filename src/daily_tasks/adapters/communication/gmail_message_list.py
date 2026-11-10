"""Responsibility: Validate one page of a Gmail `users.messages.list` response.
Public interface:
`-- GmailMessageList
    +-- messages
    `-- nextPageToken

Gmail list page wire shape; each entry holds only the message and thread ids.
"""

from collections.abc import Mapping

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class GmailMessageList:
    """Message references newest first; `messages` is absent when nothing matches."""

    messages: tuple[Mapping[str, str], ...] = ()
    nextPageToken: str | None = None  # noqa: N815 - Gmail wire field name
