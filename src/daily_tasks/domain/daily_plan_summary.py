# Responsibility: Represent an immutable DailyPlanSummary DTO.
# Public interface:
# `-- DailyPlanSummary
#     +-- late_tasks
#     +-- open_projects
#     `-- open_tasks
"""DailyPlanSummary DTO."""

from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class DailyPlanSummary:
    """Headline counts shown at the top of the daily plan."""

    open_projects: int
    open_tasks: int
    late_tasks: int

