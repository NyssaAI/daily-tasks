"""Responsibility: Define the role-named VaultReader collaborator contract.
Public interface:
`-- VaultReader
    `-- read(now)
"""

from datetime import datetime
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.planning.types import VaultSnapshot


class VaultReader(Protocol):
    """Read a vault's project plans, daily plans, and unread communication messages into a snapshot."""

    async def read(self, now: datetime) -> Result[VaultSnapshot]:
        """Build a `VaultSnapshot` as of `now`."""
        ...
