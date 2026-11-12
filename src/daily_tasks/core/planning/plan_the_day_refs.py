"""Responsibility: Choose the rows screen 1 (plan the day) lists, in display order.
Public interface:
`-- plan_the_day_refs(graph, previous_plan, suggestions)
"""

from daily_tasks.core.communications.suggestion import Suggestion
from daily_tasks.core.planning.open_task import open_task
from daily_tasks.core.planning.row_ref import RowRef
from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.state_graph import StateGraph


def plan_the_day_refs(
    graph: StateGraph, previous_plan: DailyPlan | None, suggestions: tuple[Suggestion, ...]
) -> tuple[RowRef, ...]:
    """Return task refs (deduplicated, open only) followed by one ref per pending suggestion."""
    today = graph.records.plans.get(graph.context.local_date)
    task_ids = list(today.task_ids) if today is not None else []
    if previous_plan is not None:
        task_ids.extend(entry.item_id for entry in previous_plan.entries if entry.record_kind == "task")
    refs = [RowRef(kind="task", id=task_id) for task_id in dict.fromkeys(task_ids) if open_task(graph, task_id)]
    refs.extend(RowRef(kind="suggestion", id=suggestion.id) for suggestion in suggestions)
    return tuple(refs)
