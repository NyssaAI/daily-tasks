"""Responsibility: Validate one page of a Slack `conversations.history` response.
Public interface:
`-- SlackHistoryPage
    +-- error
    +-- has_more
    +-- messages
    +-- next_cursor
    +-- ok
    `-- response_metadata

Slack Web API page wire shape; `ok: false` responses carry only `error`.
"""

from collections.abc import Mapping

from pydantic import ConfigDict, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.communications.slack_raw_message import SlackRawMessage


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class SlackHistoryPage:
    """Messages newest first, plus the pagination cursor when `has_more` is true."""

    ok: bool
    error: str | None = None
    messages: tuple[SlackRawMessage, ...] = ()
    has_more: bool = False
    response_metadata: Mapping[str, JsonValue] | None = None

    @property
    def next_cursor(self) -> str | None:
        """Cursor for the next page, or `None` on the last page."""
        if not self.has_more or self.response_metadata is None:
            return None
        cursor = self.response_metadata.get("next_cursor")
        return cursor if isinstance(cursor, str) and cursor else None
