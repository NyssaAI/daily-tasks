"""Responsibility: Define the read-only client contract for fetching inbound communication messages.
Public interface:
`-- CommunicationClient
    +-- fetch_new_messages(since)
    `-- name
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.types import FetchBatch


class CommunicationClient(Protocol):
    """Strictly read-only communication client fetching messages incrementally since cursors."""

    @property
    def name(self) -> str:
        """Source identifier matching the key in `FetchCursors.cursors` (e.g. 'gmail', 'slack')."""
        ...

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Fetch messages newer than `since` without mutating remote or local state."""
        ...
