"""Responsibility: Validate and apply a batch of user operations all-or-nothing.
Public interface:
`-- apply_operations(graph, operations, new_id, now)
"""

from collections.abc import Callable
from datetime import datetime
from uuid import UUID

from nyssa_ai_result import Result, fail, ok

from daily_tasks.core.planning.apply_operation import apply_operation
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.planning.operation_context import OperationContext
from daily_tasks.core.planning.operation_outcome import OperationOutcome
from daily_tasks.core.planning.operations import Operations
from daily_tasks.core.records.instruction_origin import InstructionOrigin
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.record_change_origin import RecordChangeOrigin
from daily_tasks.core.records.state_graph import StateGraph


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
