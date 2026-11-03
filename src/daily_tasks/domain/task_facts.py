# Responsibility: Represent an immutable TaskFacts DTO.
# Public interface:
# `-- TaskFacts
#     +-- blocked
#     +-- carried_from
#     +-- closable
#     +-- dod
#     +-- effective_assignee
#     +-- eligible
#     +-- ineligible_reason
#     +-- late
#     +-- planned_for
#     +-- responsibility
#     `-- waiting_on
"""TaskFacts DTO."""

from datetime import date

from pydantic import MISSING, UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dod_progress import DodProgress
from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class TaskFacts:
    """Computed responsibility, eligibility and planning facts for a task."""

    effective_assignee: str
    responsibility: str
    eligible: bool
    ineligible_reason: str | None | MISSING = MISSING
    late: bool
    blocked: bool
    waiting_on: tuple[UUID7, ...] | MISSING = MISSING
    planned_for: date | None
    carried_from: date | None
    dod: DodProgress
    closable: bool
