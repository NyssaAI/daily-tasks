# Responsibility: Find the day each task or blocker is planned for and where it was carried from.
# Public interface:
# `-- planned_days(plans, local_date)
"""Planned day per item: the earliest plan on or after the local date that lists it."""

from collections.abc import Mapping
from datetime import date
from uuid import UUID

from daily_tasks.domain import DailyPlan


def planned_days(plans: Mapping[date, DailyPlan], local_date: date) -> dict[UUID, tuple[date, date | None]]:
    """Return item id -> (planned day, carried_from of that entry); plans before `local_date` are ignored."""
    planned: dict[UUID, tuple[date, date | None]] = {}
    for day in sorted(plans):
        if day < local_date:
            continue
        for entry in plans[day].entries:
            planned.setdefault(entry.item_id, (day, entry.carried_from))
    return planned
