"""Responsibility: Validate one message header returned by the Gmail REST API.
Public interface:
`-- GmailHeader
    +-- name
    `-- value

Gmail `MessagePartHeader` wire shape.
"""

from pydantic import ConfigDict
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class GmailHeader:
    """RFC 2822 header as Gmail sends it."""

    name: str
    value: str = ""
