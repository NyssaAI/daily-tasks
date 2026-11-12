"""Responsibility: Define the read-only repository contract for loading dated daily plan records.
Public interface:
`-- DailyPlanRepository
    +-- fetch_plans(local_date)
    `-- name
"""

from datetime import date
from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.records.daily_plan import DailyPlan


class DailyPlanRepository(Protocol):
    """Read-only repository returning daily plans relevant to a local calendar date."""

    @property
    def name(self) -> str:
        """Stable repository identifier recorded on parsed plans and source diagnostics."""
        ...

    async def fetch_plans(self, local_date: date) -> Result[tuple[DailyPlan, ...]]:
        """Return today's plan (when present), the nearest prior plan, and future plans."""
        ...
