"""Responsibility: Build the decision-log entry for one adjudicated operation.
Public interface:
`-- decision_entry(context, action, question, decision, record_ids, before, after)

Pure decision-log entry construction; decided and recorded at the context's `now`.
"""

from collections.abc import Mapping
from uuid import UUID

from pydantic import JsonValue

from daily_tasks.domain import DecisionLogEntry
from daily_tasks.session.operation_context import OperationContext


def decision_entry(
    context: OperationContext,
    action: str,
    question: str,
    decision: str,
    record_ids: tuple[UUID, ...],
    before: Mapping[str, JsonValue] | None,
    after: Mapping[str, JsonValue] | None,
) -> DecisionLogEntry:
    """Return an entry tied to `context.operation_id`, or to no operation for a rejection."""
    return DecisionLogEntry(
        id=context.new_id(),
        session_id=context.session_id,
        question=question,
        decision=decision,
        decided_by=context.actor,
        decided_at=context.now,
        recorded_at=context.now,
        time_defaulted=False,
        original_words=context.original_words,
        origin=context.origin,
        verdict=context.verdict,
        edits=context.edits,
        action=action,
        operation_id=None if context.verdict == "reject" else context.operation_id,
        record_ids=record_ids,
        before=before,
        after=after,
        corrects=None,
    )
