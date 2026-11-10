"""Responsibility: Define the read-only port that returns daily plan records near a local date.
Public interface:
`-- DailyPlanPort
    +-- fetch_plans(around)
    `-- name

Daily-Plan-Port contract (`docs/PLANNING_SESSION_CONCEPT.md`, Ports).
"""

from datetime import date
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.domain import DailyPlan


class DailyPlanPort(Protocol):
    """Read-only source of daily plans; it never writes."""

    @property
    def name(self) -> str:
        """Configured source name."""
        ...

    async def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        """Return the plan for `around` (when present) and the most recent plan before it, newest first.

        Fails when the plans root cannot be read.
        """
        ...
