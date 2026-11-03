# Responsibility: Define how the MCP server reads one planning snapshot of the workspace.
# Public interface:
# `-- WorkspaceReader
#     `-- read(now)
"""Read contract; implementations never write and report unavailable sources inside the snapshot."""

from datetime import datetime
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.server.types import WorkspaceSnapshot


class WorkspaceReader(Protocol):
    """Builds the state graph and collects unread messages for a session starting at `now`."""

    async def read(self, now: datetime) -> Result[WorkspaceSnapshot]:
        """Return the snapshot; fails with `Unavailable` when no project-plan source could be read."""
        ...
