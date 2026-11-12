"""Responsibility: Define the collaborator contract for reading and persisting per-source fetch cursors.
Public interface:
`-- CursorStore
    +-- load()
    `-- save(cursors)
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.communications.fetch_cursors import FetchCursors


class CursorStore(Protocol):
    """Store managing per-source high-water fetch cursors in `runtime_root`."""

    def load(self) -> Result[FetchCursors]:
        """Load saved fetch cursors, or return empty cursors when none exist yet."""
        ...

    def save(self, cursors: FetchCursors) -> Result[None]:
        """Atomically replace stored fetch cursors after session confirmation."""
        ...
