"""Responsibility: Compute the carry-forward outcome from the previous daily plan.
Public interface:
`-- derive_rollover(records, local_date)

Rollover of open tasks selected on the nearest earlier plan into the plan for the local date.
"""

from datetime import date
from typing import Final
from uuid import UUID

from pydantic import TypeAdapter

from daily_tasks.domain import DailyPlan, DroppedTask, Rollover
from daily_tasks.graph.is_terminal_state import is_terminal_state
from daily_tasks.graph.types import GraphRecords

_ROLLOVER: Final[TypeAdapter[Rollover]] = TypeAdapter(Rollover)


def derive_rollover(records: GraphRecords, local_date: date) -> Rollover:
    """Return the rollover from the nearest plan before `local_date`.

    Candidates are tasks selected on that plan that are still open. Without a plan for `local_date`
    the status is `due` and every candidate is proposed as carried. With one it is `complete`: candidates
    it lists are carried, the others are dropped with a reason. Without an earlier plan the status is
    `none` and `from` is `local_date`.
    """
    earlier = [day for day in records.plans if day < local_date]
    if not earlier:
        return _rollover(local_date, "none", (), ())
    previous = records.plans[max(earlier)]
    candidates = [task_id for task_id in _task_ids(previous) if _is_open_task(records, task_id)]
    current = records.plans.get(local_date)
    if current is None:
        return _rollover(previous.local_date, "due", tuple(candidates), ())
    selected = set(_task_ids(current))
    dropped = tuple(
        DroppedTask(task_id=task_id, reason=_drop_reason(records, task_id, local_date))
        for task_id in candidates
        if task_id not in selected
    )
    carried = tuple(task_id for task_id in candidates if task_id in selected)
    return _rollover(previous.local_date, "complete", carried, dropped)


def _task_ids(plan: DailyPlan) -> list[UUID]:
    return [entry.item_id for entry in plan.entries if entry.item_type == "task"]


def _is_open_task(records: GraphRecords, task_id: UUID) -> bool:
    task = records.tasks.get(task_id)
    return task is not None and not is_terminal_state(task.state)


def _drop_reason(records: GraphRecords, task_id: UUID, local_date: date) -> str:
    target = records.tasks[task_id].target_date
    if target is not None and target < local_date:
        return "not reselected; still open and late"
    return "not reselected; still open"


def _rollover(from_date: date, status: str, carried: tuple[UUID, ...], dropped: tuple[DroppedTask, ...]) -> Rollover:
    """Build through the `from` alias; the field name `from_date` is not a constructor keyword for mypy."""
    return _ROLLOVER.validate_python({"from": from_date, "status": status, "carried": carried, "dropped": dropped})
