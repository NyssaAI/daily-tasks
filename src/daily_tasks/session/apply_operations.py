"""Responsibility: Validate and apply a batch of user operations all-or-nothing.
Public interface:
`-- apply_operations(graph, operations, new_id, now)

Pure execution of a `plan_apply` request (`docs/specs/operations.json`).

Mapping of the issue's operation names onto the spec'd operation kinds:
- `select_task` -> `assign-to-day` with today's `local_date`; `unselect_task` -> `unplan`;
- `resolve_blocker` -> `set-status` with `record_type: blocker`, `state: resolved`;
- `reorder_task` -> `assign-to-day` with another day (order within a day is the plan renderer's);
- `check_dod_item`, `accept_suggestion`, `reject_suggestion`, `add_candidate` (a `new-task`
  suggestion) -> `adjudicate_suggestions` verdicts.
"""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from nyssa_ai_result import Result, fail, ok

from daily_tasks.domain import (
    DecisionLogEntry,
    InstructionOrigin,
    Operations,
    RecordChange,
    RecordChangeOrigin,
    StateGraph,
)
from daily_tasks.session.apply_operation import apply_operation
from daily_tasks.session.operation_context import OperationContext
from daily_tasks.session.operation_outcome import OperationOutcome


def apply_operations(
    graph: StateGraph, operations: Operations, new_id: Callable[[], UUID], now: datetime
) -> Result[OperationOutcome]:
    """Apply every operation in order against the evolving graph; nothing is persisted.

    Fails with `no_operations` or with the first invalid operation's code prefixed by its index;
    then no operation of the batch is applied.
    """
    if not operations.operations:
        return fail("no_operations: the request contains no operations.", "Validation")
    current = graph
    decisions: list[DecisionLogEntry] = []
    changes: list[RecordChange] = []
    for index, operation in enumerate(operations.operations):
        row = operation.row if isinstance(operation.row, int) else 0
        context = OperationContext(
            session_id=operations.session_id,
            actor=operations.actor,
            now=now,
            new_id=new_id,
            operation_id=new_id(),
            original_words=operations.original_words,
            origin=InstructionOrigin(kind="instruction", screen_id=operations.screen_id, row=row),
            change_origin=RecordChangeOrigin(kind="decision"),
        )
        step = apply_operation(current, operation, context)
        if not step.ok:
            return fail(f"operation[{index}] {operation.kind}: {step.message}", step.category)
        current = step.value.graph
        decisions.append(step.value.decision)
        if step.value.change is not None:
            changes.append(step.value.change)
    return ok(OperationOutcome(graph=current, decisions=tuple(decisions), changes=tuple(changes)))
