# Responsibility: Define the read-only port that returns project, milestone, task and blocker records.
# Public interface:
# `-- ProjectPlanPort
#     +-- fetch_projects()
#     `-- name
"""Project-Plan-Port contract (`docs/PLANNING_SESSION_CONCEPT.md`, Ports)."""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.ports.types import ProjectPlanSnapshot


class ProjectPlanPort(Protocol):
    """Read-only source of project records; it never writes."""

    @property
    def name(self) -> str:
        """Configured source name, used in diagnostics and record `source` fields."""
        ...

    async def fetch_projects(self) -> Result[ProjectPlanSnapshot]:
        """Return every record the source holds.

        Fails when the source root cannot be read. A single malformed record does not fail the fetch;
        the adapter skips it and reports it through its logger.
        """
        ...
