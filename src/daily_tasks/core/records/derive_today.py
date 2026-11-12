"""Responsibility: Compute today's selection, available work, and work planned for later days.
Public interface:
`-- derive_today(records, task_facts, local_date)
"""

from collections.abc import Mapping
from datetime import date
from uuid import UUID

from daily_tasks.core.records.plan_item import PlanItem
from daily_tasks.core.records.task_facts import TaskFacts
from daily_tasks.core.records.today import Today
from daily_tasks.core.records.today_selection import TodaySelection
from daily_tasks.core.records.types import GraphRecords


def derive_today(records: GraphRecords, task_facts: Mapping[UUID, TaskFacts], local_date: date) -> Today:
    """Return the selection of the plan for `local_date` grouped by section."""
    selected: dict[str, list[PlanItem]] = {"my-work": [], "delegated-work": [], "follow-up-work": []}
    current = records.plans.get(local_date)
    for entry in current.entries if current is not None else ():
        selected[entry.section].append(PlanItem(record_kind=entry.record_kind, item_id=entry.item_id))
    available = tuple(task_id for task_id, facts in task_facts.items() if facts.eligible and facts.planned_for is None)
    future = {
        day: tuple(entry.item_id for entry in plan.entries) for day, plan in records.plans.items() if day > local_date
    }
    selection = TodaySelection(
        mine=tuple(selected["my-work"]),
        delegated=tuple(selected["delegated-work"]),
        follow_up=tuple(selected["follow-up-work"]),
    )
    return Today(selected=selection, available=available, future=future)
