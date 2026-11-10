"""Responsibility: Define the read-only port that fetches new messages from one communication source.
Public interface:
`-- CommunicationPort
    +-- fetch_new_messages(since)
    `-- name

Communication-Port contract (`docs/PLANNING_SESSION_CONCEPT.md`, Ports).
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.domain import FetchCursors
from daily_tasks.ports.types import FetchBatch


class CommunicationPort(Protocol):
    """Read-only message source; it never sends, drafts or modifies messages."""

    @property
    def name(self) -> str:
        """Source name; also the key of its cursor in `FetchCursors.cursors`."""
        ...

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Return messages newer than this source's cursor in `since`, with that cursor advanced.

        Cursors of other sources are returned unchanged. A message already at the cursor
        (`last_external_id`) is not returned again. Fails with the source's error category when the
        source cannot be read; the caller keeps the previous cursors.
        """
        ...
