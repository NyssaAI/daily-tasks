"""Responsibility: Plan or unplan a task or blocker for a local day inside the state graph.
Public interface:
`-- operation_planned_for(graph, record_kind, item_id, local_date)
"""

import dataclasses
from datetime import date
from uuid import UUID

from nyssa_ai_result import Result, fail, ok

from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.state_graph import StateGraph

_TERMINAL_TASK_STATES = frozenset({"completed", "cancelled"})


def operation_planned_for(
    graph: StateGraph, record_kind: RecordKind, item_id: UUID, local_date: date | None
) -> Result[tuple[StateGraph, date | None]]:
    """Return the new graph and the previous `planned_for`; `local_date=None` unplans the item.

    Fails with `unknown_record` (NotFound), `not_plannable` when the item is closed or not a task/blocker, or
    `not_planned` when unplanning an item without a planned day (Validation).
    """
    derived = graph.derived
    if record_kind == "task":
        task = graph.records.tasks.get(item_id)
        facts = derived.tasks.get(item_id)
        if task is None or facts is None:
            return fail(f"unknown_record: task {item_id} is not in the state graph.", "NotFound")
        if local_date is not None and task.state in _TERMINAL_TASK_STATES:
            return fail(f"not_plannable: task {item_id} is {task.state}.", "Validation")
        if local_date is None and facts.planned_for is None:
            return fail(f"not_planned: task {item_id} has no planned day.", "Validation")
        tasks = {**derived.tasks, item_id: dataclasses.replace(facts, planned_for=local_date)}
        new_derived = dataclasses.replace(derived, tasks=tasks)
        return ok((dataclasses.replace(graph, derived=new_derived), facts.planned_for))
    if record_kind != "blocker":
        return fail(f"not_plannable: {record_kind} {item_id} cannot be planned for a day.", "Validation")
    blocker = graph.records.blockers.get(item_id)
    blocker_facts = derived.blockers.get(item_id)
    if blocker is None or blocker_facts is None:
        return fail(f"unknown_record: blocker {item_id} is not in the state graph.", "NotFound")
    if local_date is not None and blocker.state != "open":
        return fail(f"not_plannable: blocker {item_id} is {blocker.state}.", "Validation")
    if local_date is None and blocker_facts.planned_for is None:
        return fail(f"not_planned: blocker {item_id} has no planned day.", "Validation")
    blockers = {**derived.blockers, item_id: dataclasses.replace(blocker_facts, planned_for=local_date)}
    new_derived = dataclasses.replace(derived, blockers=blockers)
    return ok((dataclasses.replace(graph, derived=new_derived), blocker_facts.planned_for))
