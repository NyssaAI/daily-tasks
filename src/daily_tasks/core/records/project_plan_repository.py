"""Responsibility: Define the read-only repository contract for loading project, milestone, task, and blocker records.
Public interface:
`-- ProjectPlanRepository
    +-- fetch_projects()
    `-- name
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.records.types import ProjectPlanSnapshot


class ProjectPlanRepository(Protocol):
    """Read-only repository returning project, milestone, task, and blocker records."""

    @property
    def name(self) -> str:
        """Stable repository identifier recorded on parsed records and source diagnostics."""
        ...

    async def fetch_projects(self) -> Result[ProjectPlanSnapshot]:
        """Return a point-in-time snapshot of all project, milestone, task, and blocker records."""
        ...
