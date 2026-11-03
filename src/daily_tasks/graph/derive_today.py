# Responsibility: Compute today's selection, available work and work planned for later days.
# Public interface:
# `-- derive_today(records, task_facts, local_date)
"""Today's sections from the plan for the local date, open unselected tasks and future plans."""

from collections.abc import Mapping
from datetime import date
from uuid import UUID

from daily_tasks.domain import PlanItem, TaskFacts, Today, TodaySelection
from daily_tasks.graph.types import GraphRecords


def derive_today(records: GraphRecords, task_facts: Mapping[UUID, TaskFacts], local_date: date) -> Today:
    """Return the selection of the plan for `local_date` grouped by section (empty without that plan).

    `available` lists open, eligible tasks not planned for any day; `future` lists items per later plan.
    """
    selected: dict[str, list[PlanItem]] = {"my-work": [], "delegated-work": [], "follow-up-work": []}
    current = records.plans.get(local_date)
    for entry in current.entries if current is not None else ():
        selected[entry.section].append(PlanItem(item_type=entry.item_type, item_id=entry.item_id))
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
