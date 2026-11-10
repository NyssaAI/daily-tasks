"""Responsibility: Apply the user's explicit verdicts to pending suggestions and prune the answered ones.
Public interface:
`-- adjudicate_suggestions(suggestions, verdicts, graph, actor, session_id, now, new_id)

Pure suggestion adjudication; there is no implicit acceptance.

Every verdict (accept, edit, reject) is logged and removes its suggestion from the pending pool;
`reject` stages no record change. Suggestions without a verdict stay pending untouched.
"""

import dataclasses
from collections.abc import Callable, Sequence
from datetime import datetime
from uuid import UUID

from nyssa_ai_result import Result, fail, ok
from pydantic import JsonValue

from daily_tasks.domain import (
    Actor,
    DecisionLogEntry,
    RecordChange,
    RecordChangeOrigin,
    StateGraph,
    SuggestionOrigin,
    Suggestions,
)
from daily_tasks.session.adjudication import Adjudication
from daily_tasks.session.adjudication_effect import adjudication_effect
from daily_tasks.session.adjudication_verdict import AdjudicationVerdict
from daily_tasks.session.decision_entry import decision_entry
from daily_tasks.session.operation_context import OperationContext


def adjudicate_suggestions(
    suggestions: Suggestions,
    verdicts: Sequence[AdjudicationVerdict],
    graph: StateGraph,
    actor: Actor,
    session_id: UUID,
    now: datetime,
    new_id: Callable[[], UUID],
) -> Result[Adjudication]:
    """Return the pruned pool, updated graph, decision entries and staged changes.

    Fails with `unknown_suggestion` (NotFound), `duplicate_verdict`, `invalid_edits` (Validation)
    or the first effect's code; then nothing is pruned, logged or staged.
    """
    pending = {s.id: s for s in suggestions.suggestions}
    seen: set[UUID] = set()
    current = graph
    decisions: list[DecisionLogEntry] = []
    changes: list[RecordChange] = []
    for verdict in verdicts:
        suggestion = pending.get(verdict.suggestion_id)
        if suggestion is None:
            return fail(f"unknown_suggestion: {verdict.suggestion_id} is not pending.", "NotFound")
        if verdict.suggestion_id in seen:
            return fail(f"duplicate_verdict: {verdict.suggestion_id} was answered twice.", "Validation")
        if (verdict.verdict == "edit") != bool(verdict.edits):
            return fail(f"invalid_edits: only 'edit' carries edits ({verdict.suggestion_id}).", "Validation")
        seen.add(verdict.suggestion_id)
        context = OperationContext(
            session_id=session_id,
            actor=actor,
            now=now,
            new_id=new_id,
            operation_id=new_id(),
            original_words=verdict.original_words,
            origin=SuggestionOrigin(
                kind="suggestion",
                suggestion_id=suggestion.id,
                screen_id=verdict.screen_id,
                row=verdict.row,
                message_ids=suggestion.source_message_ids,
            ),
            change_origin=RecordChangeOrigin(kind="decision", suggestion_id=suggestion.id),
            verdict=verdict.verdict,
            edits=verdict.edits,
        )
        if verdict.verdict == "reject":
            question = f"{suggestion.kind} suggestion: {suggestion.rationale}"
            decisions.append(decision_entry(context, "reject-suggestion", question, "Rejected.", (), None, None))
            continue
        proposed: dict[str, JsonValue] = {**suggestion.proposed, **(verdict.edits or {})}
        step = adjudication_effect(current, suggestion, proposed, context)
        if not step.ok:
            return fail(f"suggestion {suggestion.id}: {step.message}", step.category)
        current = step.value.graph
        decisions.append(step.value.decision)
        if step.value.change is not None:
            changes.append(step.value.change)
    remaining = tuple(s for s in suggestions.suggestions if s.id not in seen)
    updated_at = now if seen else suggestions.updated_at
    pruned = dataclasses.replace(suggestions, suggestions=remaining, updated_at=updated_at)
    return ok(Adjudication(suggestions=pruned, graph=current, decisions=tuple(decisions), changes=tuple(changes)))
