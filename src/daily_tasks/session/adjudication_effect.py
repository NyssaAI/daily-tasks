"""Responsibility: Turn one accepted or edited suggestion into a validated graph change and staged record change.
Public interface:
`-- adjudication_effect(graph, suggestion, proposed, context)

Pure suggestion effects by kind (`docs/specs/suggestions.json` `_kinds`).

- `status` and `blocker` with `action: resolve` -> validated `set-status`;
- `dod` -> checks DoD items (`proposed.dod` maps item id to true) and updates DoD progress;
- `new-task` (the issue's `add_candidate`) and blocker `link`/`create` -> staged record change only.
"""

import dataclasses
from collections.abc import Mapping
from typing import Final, Literal
from uuid import UUID

from nyssa_ai_result import Result, fail, ok
from pydantic import JsonValue

from daily_tasks.domain import SetStatus, StateGraph, Suggestion
from daily_tasks.session.decision_entry import decision_entry
from daily_tasks.session.operation_context import OperationContext
from daily_tasks.session.operation_record_change import operation_record_change
from daily_tasks.session.operation_set_state import operation_set_state
from daily_tasks.session.operation_status_rule import operation_status_rule
from daily_tasks.session.operation_step import OperationStep

type _RecordType = Literal["project", "milestone", "task", "blocker"]
_RECORD_TYPES: Final[Mapping[str, _RecordType]] = {
    "project": "project",
    "milestone": "milestone",
    "task": "task",
    "blocker": "blocker",
}


def adjudication_effect(
    graph: StateGraph, suggestion: Suggestion, proposed: Mapping[str, JsonValue], context: OperationContext
) -> Result[OperationStep]:
    """Apply `proposed` (the suggestion's proposal merged with the user's edits).

    Fails with `missing_target`, `invalid_proposal` (Validation) or the `set-status` rule codes.
    """
    question = f"{suggestion.kind} suggestion: {suggestion.rationale}"
    decision = "Accepted." if context.verdict == "accept" else "Accepted with edits."
    if suggestion.kind == "new-task":
        record_id = context.new_id()
        change = operation_record_change(graph, context, "task", record_id, None, proposed)
        entry = decision_entry(context, "create-task", question, decision, (record_id,), None, proposed)
        return ok(OperationStep(graph=graph, decision=entry, change=change))
    target = suggestion.target
    record_type = None if target is None else _RECORD_TYPES.get(target.record_type)
    if target is None or record_type is None:
        return fail(f"missing_target: suggestion {suggestion.id} has no record target.", "Validation")
    state = _proposed_state(suggestion, proposed)
    if state is not None:
        operation = SetStatus(
            kind="set-status", record_type=record_type, record_id=target.record_id, state=state, activity_at=context.now
        )
        checked = operation_status_rule(graph, operation)
        if not checked.ok:
            return checked
        before: Mapping[str, JsonValue] = {"state": checked.value}
        after: Mapping[str, JsonValue] = {"state": state}
        new_graph = operation_set_state(graph, record_type, target.record_id, state)
        action = "resolve-blocker" if suggestion.kind == "blocker" else "set-status"
    elif suggestion.kind == "dod":
        dod = proposed.get("dod")
        if not isinstance(dod, Mapping) or not dod:
            return fail(f"invalid_proposal: dod suggestion {suggestion.id} names no DoD items.", "Validation")
        before = {"dod": {item: False for item in dod}}
        after = {"dod": dict(dod)}
        new_graph = _check_dod(graph, target.record_id, sum(1 for v in dod.values() if v is True))
        action = "check-dod"
    else:
        before = suggestion.current or {}
        after = proposed
        new_graph = graph
        action = f"{suggestion.kind}-{proposed.get('action', 'update')}"
    change = operation_record_change(graph, context, record_type, target.record_id, before, after)
    entry = decision_entry(context, action, question, decision, (target.record_id,), before, after)
    return ok(OperationStep(graph=new_graph, decision=entry, change=change))


def _proposed_state(suggestion: Suggestion, proposed: Mapping[str, JsonValue]) -> str | None:
    if suggestion.kind == "status":
        state = proposed.get("state")
        return state if isinstance(state, str) else None
    if suggestion.kind == "blocker" and proposed.get("action") == "resolve":
        return "resolved"
    return None


def _check_dod(graph: StateGraph, task_id: UUID, checked: int) -> StateGraph:
    facts = graph.derived.tasks.get(task_id)
    if facts is None:
        return graph
    done = min(facts.dod.total, facts.dod.done + checked)
    new_facts = dataclasses.replace(facts, dod=dataclasses.replace(facts.dod, done=done))
    tasks = {**graph.derived.tasks, task_id: new_facts}
    return dataclasses.replace(graph, derived=dataclasses.replace(graph.derived, tasks=tasks))
