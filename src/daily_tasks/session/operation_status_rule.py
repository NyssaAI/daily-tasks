# Responsibility: Check a requested state change against the operations.json `_rules`.
# Public interface:
# +-- ALLOWED_STATES
# `-- operation_status_rule(graph, operation)
"""Pure validation of `set-status`: allowed states, completion and cancellation preconditions."""

from collections.abc import Mapping
from typing import Final
from uuid import UUID

from nyssa_ai_result import Result, fail, ok
from pydantic import MISSING

from daily_tasks.domain import SetStatus, StateGraph

ALLOWED_STATES: Final[Mapping[str, frozenset[str]]] = {
    "task": frozenset({"not-started", "in-progress", "completed", "cancelled"}),
    "blocker": frozenset({"open", "resolved"}),
    "milestone": frozenset({"in-progress", "completed", "cancelled"}),
    "project": frozenset({"in-progress", "completed", "cancelled"}),
}
_TERMINAL = frozenset({"completed", "cancelled"})


def operation_status_rule(graph: StateGraph, operation: SetStatus) -> Result[str]:
    """Return the record's current state when the change is allowed.

    Fails with `unknown_record` (NotFound), or with `invalid_state`, `unchanged_state`,
    `dod_incomplete`, `open_blockers`, `open_children` (Validation).
    """
    current = _current_state(graph, operation)
    if current is None:
        return fail(
            f"unknown_record: {operation.record_type} {operation.record_id} is not in the state graph.", "NotFound"
        )
    if operation.state not in ALLOWED_STATES[operation.record_type]:
        return fail(f"invalid_state: {operation.record_type} cannot be set to '{operation.state}'.", "Validation")
    if operation.state == current:
        return fail(
            f"unchanged_state: {operation.record_type} {operation.record_id} is already {current}.", "Validation"
        )
    if operation.record_type == "task" and operation.state == "completed":
        return _task_completion(graph, operation.record_id).then(lambda _: ok(current))
    if operation.record_type in ("milestone", "project") and operation.state in _TERMINAL:
        return _children_dispositioned(graph, operation).then(lambda _: ok(current))
    return ok(current)


def _current_state(graph: StateGraph, operation: SetStatus) -> str | None:
    records = graph.records
    record_id = operation.record_id
    if operation.record_type == "task":
        task = records.tasks.get(record_id)
        return None if task is None else task.state
    if operation.record_type == "blocker":
        blocker = records.blockers.get(record_id)
        return None if blocker is None else blocker.state
    if operation.record_type == "milestone":
        milestone = records.milestones.get(record_id)
        return None if milestone is None else milestone.state
    project = records.projects.get(record_id)
    return None if project is None else project.state


def _task_completion(graph: StateGraph, task_id: UUID) -> Result[None]:
    facts = graph.derived.tasks.get(task_id)
    if facts is not None and facts.dod.done < facts.dod.total:
        return fail(
            f"dod_incomplete: task {task_id} has {facts.dod.done}/{facts.dod.total} DoD items checked.", "Validation"
        )
    open_blockers = [
        b for b in graph.index.blocked_by.get(task_id, ()) if _blocker_state(graph, b) not in (None, "resolved")
    ]
    if open_blockers:
        return fail(f"open_blockers: task {task_id} is blocked by {len(open_blockers)} open blocker(s).", "Validation")
    return ok(None)


def _blocker_state(graph: StateGraph, blocker_id: UUID) -> str | None:
    blocker = graph.records.blockers.get(blocker_id)
    return None if blocker is None else blocker.state


def _children_dispositioned(graph: StateGraph, operation: SetStatus) -> Result[None]:
    dispositions = {} if operation.child_dispositions is MISSING else operation.child_dispositions
    records = graph.records
    if operation.record_type == "milestone":
        children = {tid: t.state for tid, t in records.tasks.items() if t.milestone_id == operation.record_id}
    else:
        children = {mid: m.state for mid, m in records.milestones.items() if m.project_id == operation.record_id}
    open_children = [cid for cid, state in children.items() if state not in _TERMINAL and cid not in dispositions]
    if open_children:
        return fail(
            f"open_children: {operation.record_type} {operation.record_id} has {len(open_children)} "
            "non-terminal child record(s) without a disposition.",
            "Validation",
        )
    return ok(None)
