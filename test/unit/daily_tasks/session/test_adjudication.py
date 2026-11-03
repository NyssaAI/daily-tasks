# Responsibility: Prove operations and suggestion verdicts are validated, applied, pruned and logged explicitly.
# Public interface:
# (none)
"""Adjudication engine against the `docs/specs` state graph, operations and suggestions examples."""

import dataclasses
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime
from itertools import count
from typing import Literal
from uuid import UUID

import pytest
from pydantic import JsonValue, TypeAdapter

from conftest import load_spec
from daily_tasks.domain import Actor, Operations, StateGraph, Suggestions
from daily_tasks.session.adjudicate_suggestions import adjudicate_suggestions
from daily_tasks.session.adjudication_verdict import AdjudicationVerdict
from daily_tasks.session.apply_operations import apply_operations

NOW = datetime(2026, 11, 3, 14, 24, tzinfo=UTC)
ACTOR = Actor(kind="person", id="jordan@example.com")
SESSION = UUID("019a4b2c-9000-7000-8000-0000000000a1")
GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
FETCH_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000004")
README_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000007")
REVIEW_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000008")
OAUTH_BLOCKER = UUID("019a4b2c-1f00-7a10-8000-000000000005")
SPIKE_MILESTONE = UUID("019a4b2c-1f00-7a10-8000-000000000002")
CONNECTORS_MILESTONE = UUID("019a4b2c-1f00-7a10-8000-000000000012")
STATUS_SUGGESTION = UUID("019a4b2c-9000-7000-8000-0000000000b4")
BLOCKER_SUGGESTION = UUID("019a4b2c-9000-7000-8000-0000000000b5")
GMAIL_PATH = "2026.10.20-daily-tasks-mcp-server/m2-planning-session-spike/t1-wire-gmail-connector.md"


def _graph() -> StateGraph:
    return TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))


def _suggestions() -> Suggestions:
    return TypeAdapter(Suggestions).validate_python(load_spec("suggestions.json"))


def _ids() -> Callable[[], UUID]:
    numbers: Iterator[int] = count(1)
    return lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")


def _request(*operations: dict[str, JsonValue]) -> Operations:
    return TypeAdapter(Operations).validate_python(
        {
            "session_id": str(SESSION),
            "screen_id": "s2",
            "original_words": "words",
            "actor": {"kind": "person", "id": "jordan@example.com"},
            "operations": list(operations),
        }
    )


def _status(record_type: str, record_id: UUID, state: str, **extra: JsonValue) -> dict[str, JsonValue]:
    operation: dict[str, JsonValue] = {
        "kind": "set-status",
        "row": 1,
        "record_type": record_type,
        "record_id": str(record_id),
        "state": state,
        "activity_at": "2026-11-03T14:24:00Z",
    }
    return {**operation, **extra}


def _verdict(
    suggestion_id: UUID, verdict: Literal["accept", "edit", "reject"], edits: dict[str, JsonValue] | None = None
) -> AdjudicationVerdict:
    return AdjudicationVerdict(
        suggestion_id=suggestion_id, verdict=verdict, screen_id="s1", row=4, original_words=f"4 {verdict}", edits=edits
    )


def test_apply_operations_assign_to_day_moves_plan_without_record_change() -> None:
    request = _request(
        {
            "kind": "assign-to-day",
            "row": 13,
            "item_type": "task",
            "item_id": str(README_TASK),
            "local_date": "2026-11-06",
        }
    )

    result = apply_operations(_graph(), request, _ids(), NOW)

    assert result.ok
    assert result.value.graph.derived.tasks[README_TASK].planned_for == date(2026, 11, 6)
    assert result.value.changes == ()
    (entry,) = result.value.decisions
    assert (entry.action, entry.before, entry.after) == (
        "assign-to-day",
        {"planned_for": "2026-11-05"},
        {"planned_for": "2026-11-06"},
    )
    assert entry.origin.kind == "instruction" and entry.verdict is None and entry.decided_by == ACTOR


def test_apply_operations_unplan_blocker_clears_planned_day() -> None:
    request = _request({"kind": "unplan", "row": 18, "item_type": "blocker", "item_id": str(OAUTH_BLOCKER)})

    result = apply_operations(_graph(), request, _ids(), NOW)

    assert result.ok
    assert result.value.graph.derived.blockers[OAUTH_BLOCKER].planned_for is None
    assert result.value.decisions[0].after == {"planned_for": None}


def test_apply_operations_resolve_blocker_and_reassign_stage_record_changes() -> None:
    request = _request(
        _status("blocker", OAUTH_BLOCKER, "resolved"),
        {
            "kind": "reassign",
            "row": 18,
            "item_type": "blocker",
            "item_id": str(OAUTH_BLOCKER),
            "owner": "dana@example.com",
        },
    )

    result = apply_operations(_graph(), request, _ids(), NOW)

    assert result.ok
    blocker = result.value.graph.records.blockers[OAUTH_BLOCKER]
    assert (blocker.state, blocker.owner) == ("resolved", "dana@example.com")
    assert [(c.before, c.after, c.status) for c in result.value.changes] == [
        ({"state": "open"}, {"state": "resolved"}, "staged"),
        ({"owner": "jordan@example.com"}, {"owner": "dana@example.com"}, "staged"),
    ]
    assert [d.action for d in result.value.decisions] == ["set-status", "reassign"]


def test_apply_operations_set_status_in_progress_stages_change_with_file_hash() -> None:
    graph = _graph()
    request = _request(_status("task", FETCH_TASK, "in-progress"))

    result = apply_operations(graph, request, _ids(), NOW)

    assert result.ok
    assert result.value.graph.records.tasks[FETCH_TASK].state == "in-progress"
    assert graph.records.tasks[FETCH_TASK].state == "not-started"
    (change,) = result.value.changes
    assert change.operation_id == result.value.decisions[0].operation_id


def test_apply_operations_reassign_task_records_file_path_and_hash() -> None:
    request = _request(
        {"kind": "reassign", "row": 3, "item_type": "task", "item_id": str(GMAIL_TASK), "owner": "alex@example.com"}
    )

    result = apply_operations(_graph(), request, _ids(), NOW)

    assert result.ok
    (change,) = result.value.changes
    assert (change.path, change.expected_hash) == (GMAIL_PATH, "sha256:31be09aa77")


@pytest.mark.parametrize(
    ("operation", "code"),
    [
        (_status("task", FETCH_TASK, "open"), "invalid_state"),
        (_status("blocker", OAUTH_BLOCKER, "completed"), "invalid_state"),
        (_status("task", FETCH_TASK, "not-started"), "unchanged_state"),
        (_status("task", FETCH_TASK, "completed"), "dod_incomplete"),
        (_status("milestone", SPIKE_MILESTONE, "completed"), "open_children"),
        (_status("task", UUID("019a4b2c-1f00-7a10-8000-0000000000ff"), "completed"), "unknown_record"),
        (
            {"kind": "unplan", "row": 17, "item_type": "task", "item_id": "019a4b2c-1f00-7a10-8000-000000000017"},
            "unknown_record",
        ),
        (
            {"kind": "unplan", "row": 1, "item_type": "blocker", "item_id": "019a4b2c-1f00-7a10-8000-000000000016"},
            "not_planned",
        ),
        (
            {"kind": "reassign", "row": 1, "item_type": "task", "item_id": str(GMAIL_TASK), "owner": "dana"},
            "invalid_owner",
        ),
    ],
)
def test_apply_operations_invalid_operation_refused_with_code(operation: dict[str, JsonValue], code: str) -> None:
    result = apply_operations(_graph(), _request(operation), _ids(), NOW)

    assert not result.ok
    assert code in result.message


def test_apply_operations_completed_with_open_blocker_refused() -> None:
    graph = _graph()
    facts = graph.derived.tasks[GMAIL_TASK]
    all_done = dataclasses.replace(facts, dod=dataclasses.replace(facts.dod, done=facts.dod.total))
    tasks = {**graph.derived.tasks, GMAIL_TASK: all_done}
    graph = dataclasses.replace(graph, derived=dataclasses.replace(graph.derived, tasks=tasks))

    result = apply_operations(graph, _request(_status("task", GMAIL_TASK, "completed")), _ids(), NOW)

    assert not result.ok
    assert "open_blockers" in result.message


def test_apply_operations_milestone_with_dispositions_completes() -> None:
    graph = _graph()
    children = [str(t) for t, task in graph.records.tasks.items() if task.milestone_id == CONNECTORS_MILESTONE]
    operation = _status(
        "milestone", CONNECTORS_MILESTONE, "completed", child_dispositions={c: "moved" for c in children}
    )

    result = apply_operations(graph, _request(operation), _ids(), NOW)

    assert result.ok
    assert result.value.graph.records.milestones[CONNECTORS_MILESTONE].state == "completed"


def test_apply_operations_spec_request_invalid_operation_applies_nothing() -> None:
    request = TypeAdapter(Operations).validate_python(load_spec("operations.json"))

    result = apply_operations(_graph(), request, _ids(), NOW)

    assert not result.ok
    assert result.message.startswith("operation[3] unplan: unknown_record")


def test_adjudicate_suggestions_accept_status_prunes_logs_and_stages_change() -> None:
    result = adjudicate_suggestions(
        _suggestions(), [_verdict(STATUS_SUGGESTION, "accept")], _graph(), ACTOR, SESSION, NOW, _ids()
    )

    assert result.ok
    assert [s.id for s in result.value.suggestions.suggestions] == [BLOCKER_SUGGESTION]
    assert result.value.suggestions.updated_at == NOW
    assert result.value.graph.records.tasks[FETCH_TASK].state == "in-progress"
    (entry,) = result.value.decisions
    assert (entry.verdict, entry.action, entry.origin.kind) == ("accept", "set-status", "suggestion")
    (change,) = result.value.changes
    assert change.origin.suggestion_id == STATUS_SUGGESTION and change.after == {"state": "in-progress"}


def test_adjudicate_suggestions_reject_logs_without_record_change() -> None:
    result = adjudicate_suggestions(
        _suggestions(), [_verdict(BLOCKER_SUGGESTION, "reject")], _graph(), ACTOR, SESSION, NOW, _ids()
    )

    assert result.ok
    assert [s.id for s in result.value.suggestions.suggestions] == [STATUS_SUGGESTION]
    assert result.value.changes == ()
    (entry,) = result.value.decisions
    assert (entry.verdict, entry.action, entry.operation_id, entry.record_ids) == (
        "reject",
        "reject-suggestion",
        None,
        (),
    )


def test_adjudicate_suggestions_accept_blocker_resolve_resolves_blocker() -> None:
    result = adjudicate_suggestions(
        _suggestions(), [_verdict(BLOCKER_SUGGESTION, "accept")], _graph(), ACTOR, SESSION, NOW, _ids()
    )

    assert result.ok
    assert result.value.graph.records.blockers[UUID("019a4b2c-1f00-7a10-8000-000000000016")].state == "resolved"
    assert result.value.decisions[0].action == "resolve-blocker"


def test_adjudicate_suggestions_edit_applies_edited_state() -> None:
    edits: dict[str, JsonValue] = {"state": "cancelled"}

    result = adjudicate_suggestions(
        _suggestions(), [_verdict(STATUS_SUGGESTION, "edit", edits)], _graph(), ACTOR, SESSION, NOW, _ids()
    )

    assert result.ok
    assert result.value.graph.records.tasks[FETCH_TASK].state == "cancelled"
    assert result.value.decisions[0].edits == edits


def test_adjudicate_suggestions_no_verdicts_keeps_everything_pending() -> None:
    suggestions = _suggestions()

    result = adjudicate_suggestions(suggestions, [], _graph(), ACTOR, SESSION, NOW, _ids())

    assert result.ok
    assert result.value.suggestions == suggestions
    assert (result.value.decisions, result.value.changes) == ((), ())


def test_adjudicate_suggestions_dod_then_complete_task_succeeds() -> None:
    dod_item = "019a4b2c-1f00-7a10-8000-0000000000d4"
    suggestion = TypeAdapter(Suggestions).validate_python(
        {
            **_suggestion_pool(),
            "suggestions": [
                {
                    "id": "019a4b2c-9000-7000-8000-0000000000b6",
                    "kind": "dod",
                    "created_at": "2026-11-03T14:09:30Z",
                    "created_in_session": str(SESSION),
                    "source_message_ids": ["gmail:1"],
                    "evidence": "review done",
                    "rationale": "The review is done.",
                    "target": {
                        "record_type": "task",
                        "record_id": str(REVIEW_TASK),
                        "expected_updated_at": "2026-11-01T16:00:00Z",
                    },
                    "current": {"dod": {dod_item: False}},
                    "proposed": {"dod": {dod_item: True}},
                    "validation": {"ok": True, "issues": []},
                }
            ],
        }
    )
    verdict = _verdict(UUID("019a4b2c-9000-7000-8000-0000000000b6"), "accept")

    adjudicated = adjudicate_suggestions(suggestion, [verdict], _graph(), ACTOR, SESSION, NOW, _ids())
    assert adjudicated.ok
    completed = apply_operations(
        adjudicated.value.graph, _request(_status("task", REVIEW_TASK, "completed")), _ids(), NOW
    )

    assert adjudicated.value.decisions[0].action == "check-dod"
    assert adjudicated.value.suggestions.suggestions == ()
    assert completed.ok


def _suggestion_pool() -> dict[str, JsonValue]:
    return {"workspace_root": "D:/vaults/work", "updated_at": "2026-11-03T14:20:05Z", "no_suggestion_message_ids": []}


@pytest.mark.parametrize(
    ("verdicts", "code"),
    [
        ([_verdict(UUID("019a4b2c-9000-7000-8000-0000000000ff"), "accept")], "unknown_suggestion"),
        ([_verdict(STATUS_SUGGESTION, "reject"), _verdict(STATUS_SUGGESTION, "accept")], "duplicate_verdict"),
        ([_verdict(STATUS_SUGGESTION, "edit")], "invalid_edits"),
    ],
)
def test_adjudicate_suggestions_invalid_verdicts_refused(verdicts: list[AdjudicationVerdict], code: str) -> None:
    result = adjudicate_suggestions(_suggestions(), verdicts, _graph(), ACTOR, SESSION, NOW, _ids())

    assert not result.ok
    assert code in result.message
