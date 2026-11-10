"""Responsibility: Validate one user operation against the state graph and apply it without side effects.
Public interface:
`-- apply_operation(graph, operation, context)

Pure execution of one `assign-to-day`, `unplan`, `set-status` or `reassign` operation.

`assign-to-day` and `unplan` change only the daily plan (no record change is staged);
`set-status` and `reassign` stage a record change for the record file.
"""

import dataclasses

from nyssa_ai_result import Result, fail, ok

from daily_tasks.domain import AssignToDay, Operation, Reassign, SetStatus, StateGraph, Unplan
from daily_tasks.session.decision_entry import decision_entry
from daily_tasks.session.operation_context import OperationContext
from daily_tasks.session.operation_planned_for import operation_planned_for
from daily_tasks.session.operation_record_change import operation_record_change
from daily_tasks.session.operation_set_state import operation_set_state
from daily_tasks.session.operation_status_rule import operation_status_rule
from daily_tasks.session.operation_step import OperationStep


def apply_operation(graph: StateGraph, operation: Operation, context: OperationContext) -> Result[OperationStep]:
    """Return the new graph, its decision entry and the staged change, or the first rule violation.

    Fails with the codes of `operation_planned_for`, `operation_status_rule`, or `invalid_owner`.
    """
    match operation:
        case AssignToDay() | Unplan():
            return _plan(graph, operation, context)
        case SetStatus():
            return _set_status(graph, operation, context)
        case Reassign():
            return _reassign(graph, operation, context)


def _plan(graph: StateGraph, operation: AssignToDay | Unplan, context: OperationContext) -> Result[OperationStep]:
    local_date = operation.local_date if isinstance(operation, AssignToDay) else None
    planned = operation_planned_for(graph, operation.item_type, operation.item_id, local_date)
    if not planned.ok:
        return planned
    new_graph, previous = planned.value
    after = local_date.isoformat() if local_date is not None else None
    decision = f"Moved to {after}." if after is not None else "Removed from its planned day."
    entry = decision_entry(
        context,
        action=operation.kind,
        question=f"Which day should {operation.item_type} {operation.item_id} be planned for?",
        decision=decision,
        record_ids=(operation.item_id,),
        before={"planned_for": previous.isoformat() if previous is not None else None},
        after={"planned_for": after},
    )
    return ok(OperationStep(graph=new_graph, decision=entry, change=None))


def _set_status(graph: StateGraph, operation: SetStatus, context: OperationContext) -> Result[OperationStep]:
    checked = operation_status_rule(graph, operation)
    if not checked.ok:
        return checked
    before = {"state": checked.value}
    after = {"state": operation.state}
    entry = decision_entry(
        context,
        action=operation.kind,
        question=f"Set {operation.record_type} {operation.record_id} to {operation.state}?",
        decision=f"Set to {operation.state}.",
        record_ids=(operation.record_id,),
        before=before,
        after=after,
    )
    change = operation_record_change(graph, context, operation.record_type, operation.record_id, before, after)
    new_graph = operation_set_state(graph, operation.record_type, operation.record_id, operation.state)
    return ok(OperationStep(graph=new_graph, decision=entry, change=change))


def _reassign(graph: StateGraph, operation: Reassign, context: OperationContext) -> Result[OperationStep]:
    owner = operation.owner.strip()
    if "@" not in owner:
        return fail(f"invalid_owner: '{operation.owner}' is not an email address.", "Validation")
    records = graph.records
    if operation.item_type == "task":
        task = records.tasks.get(operation.item_id)
        if task is None:
            return fail(f"unknown_record: task {operation.item_id} is not in the state graph.", "NotFound")
        previous = task.owner
        tasks = {**records.tasks, operation.item_id: dataclasses.replace(task, owner=owner)}
        new_graph = dataclasses.replace(graph, records=dataclasses.replace(records, tasks=tasks))
    else:
        blocker = records.blockers.get(operation.item_id)
        if blocker is None:
            return fail(f"unknown_record: blocker {operation.item_id} is not in the state graph.", "NotFound")
        previous = blocker.owner
        blockers = {**records.blockers, operation.item_id: dataclasses.replace(blocker, owner=owner)}
        derived = graph.derived
        facts = derived.blockers.get(operation.item_id)
        blocker_facts = derived.blockers
        if facts is not None:
            blocker_facts = {**derived.blockers, operation.item_id: dataclasses.replace(facts, owner=owner)}
        new_graph = dataclasses.replace(
            graph,
            records=dataclasses.replace(records, blockers=blockers),
            derived=dataclasses.replace(derived, blockers=blocker_facts),
        )
    entry = decision_entry(
        context,
        action=operation.kind,
        question=f"Who owns {operation.item_type} {operation.item_id}?",
        decision=f"Reassigned to {owner}.",
        record_ids=(operation.item_id,),
        before={"owner": previous},
        after={"owner": owner},
    )
    change = operation_record_change(
        graph, context, operation.item_type, operation.item_id, {"owner": previous}, {"owner": owner}
    )
    return ok(OperationStep(graph=new_graph, decision=entry, change=change))
