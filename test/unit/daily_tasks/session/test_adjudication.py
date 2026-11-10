"""Responsibility: Prove operations and suggestion verdicts are validated, applied, pruned and logged explicitly.
Public interface:
+-- test_apply_operations_assign_to_day_moves_plan_without_record_change()
+-- test_apply_operations_completed_with_open_blocker_refused()
+-- test_apply_operations_invalid_operation_refused_with_code(operation, code)
+-- test_apply_operations_milestone_with_dispositions_completes()
+-- test_apply_operations_reassign_task_records_file_path_and_hash()
+-- test_apply_operations_resolve_blocker_and_reassign_stage_record_changes()
+-- test_apply_operations_set_status_in_progress_stages_change_with_file_hash()
+-- test_apply_operations_spec_request_invalid_operation_applies_nothing()
`-- test_apply_operations_unplan_blocker_clears_planned_day()

Adjudication engine against the `docs/specs` state graph, operations and suggestions examples.
"""

import dataclasses
from collections.abc import Callable, Iterator
from datetime import UTC, date, datetime
from itertools import count
from uuid import UUID

import pytest
from pydantic import JsonValue, TypeAdapter

from conftest import load_spec
from daily_tasks.domain import Actor, Operations, StateGraph
from daily_tasks.session.apply_operations import apply_operations

_NOW = datetime(2026, 11, 3, 14, 24, tzinfo=UTC)
_ACTOR = Actor(kind="person", id="jordan@example.com")
_SESSION = UUID("019a4b2c-9000-7000-8000-0000000000a1")
_GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
_FETCH_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000004")
_README_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000007")
_OAUTH_BLOCKER = UUID("019a4b2c-1f00-7a10-8000-000000000005")
_SPIKE_MILESTONE = UUID("019a4b2c-1f00-7a10-8000-000000000002")
_CONNECTORS_MILESTONE = UUID("019a4b2c-1f00-7a10-8000-000000000012")
_GMAIL_PATH = "2026.10.20-daily-tasks-mcp-server/m2-planning-session-spike/t1-wire-gmail-connector.md"


def _graph() -> StateGraph:
    return TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))


def _ids() -> Callable[[], UUID]:
    numbers: Iterator[int] = count(1)
    return lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}")


def _request(*operations: dict[str, JsonValue]) -> Operations:
    return TypeAdapter(Operations).validate_python(
        {
            "session_id": str(_SESSION),
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


def test_apply_operations_assign_to_day_moves_plan_without_record_change() -> None:
    request = _request(
        {
            "kind": "assign-to-day",
            "row": 13,
            "item_type": "task",
            "item_id": str(_README_TASK),
            "local_date": "2026-11-06",
        }
    )

    result = apply_operations(_graph(), request, _ids(), _NOW)

    assert result.ok
    assert result.value.graph.derived.tasks[_README_TASK].planned_for == date(2026, 11, 6)
    assert result.value.changes == ()
    (entry,) = result.value.decisions
    assert (entry.action, entry.before, entry.after) == (
        "assign-to-day",
        {"planned_for": "2026-11-05"},
        {"planned_for": "2026-11-06"},
    )
    assert entry.origin.kind == "instruction" and entry.verdict is None and entry.decided_by == _ACTOR


def test_apply_operations_unplan_blocker_clears_planned_day() -> None:
    request = _request({"kind": "unplan", "row": 18, "item_type": "blocker", "item_id": str(_OAUTH_BLOCKER)})

    result = apply_operations(_graph(), request, _ids(), _NOW)

    assert result.ok
    assert result.value.graph.derived.blockers[_OAUTH_BLOCKER].planned_for is None
    assert result.value.decisions[0].after == {"planned_for": None}


def test_apply_operations_resolve_blocker_and_reassign_stage_record_changes() -> None:
    request = _request(
        _status("blocker", _OAUTH_BLOCKER, "resolved"),
        {
            "kind": "reassign",
            "row": 18,
            "item_type": "blocker",
            "item_id": str(_OAUTH_BLOCKER),
            "owner": "dana@example.com",
        },
    )

    result = apply_operations(_graph(), request, _ids(), _NOW)

    assert result.ok
    blocker = result.value.graph.records.blockers[_OAUTH_BLOCKER]
    assert (blocker.state, blocker.owner) == ("resolved", "dana@example.com")
    assert [(c.before, c.after, c.status) for c in result.value.changes] == [
        ({"state": "open"}, {"state": "resolved"}, "staged"),
        ({"owner": "jordan@example.com"}, {"owner": "dana@example.com"}, "staged"),
    ]
    assert [d.action for d in result.value.decisions] == ["set-status", "reassign"]


def test_apply_operations_set_status_in_progress_stages_change_with_file_hash() -> None:
    graph = _graph()
    request = _request(_status("task", _FETCH_TASK, "in-progress"))

    result = apply_operations(graph, request, _ids(), _NOW)

    assert result.ok
    assert result.value.graph.records.tasks[_FETCH_TASK].state == "in-progress"
    assert graph.records.tasks[_FETCH_TASK].state == "not-started"
    (change,) = result.value.changes
    assert change.operation_id == result.value.decisions[0].operation_id


def test_apply_operations_reassign_task_records_file_path_and_hash() -> None:
    request = _request(
        {"kind": "reassign", "row": 3, "item_type": "task", "item_id": str(_GMAIL_TASK), "owner": "alex@example.com"}
    )

    result = apply_operations(_graph(), request, _ids(), _NOW)

    assert result.ok
    (change,) = result.value.changes
    assert (change.path, change.expected_hash) == (_GMAIL_PATH, "sha256:31be09aa77")


@pytest.mark.parametrize(
    ("operation", "code"),
    [
        (_status("task", _FETCH_TASK, "open"), "invalid_state"),
        (_status("blocker", _OAUTH_BLOCKER, "completed"), "invalid_state"),
        (_status("task", _FETCH_TASK, "not-started"), "unchanged_state"),
        (_status("task", _FETCH_TASK, "completed"), "dod_incomplete"),
        (_status("milestone", _SPIKE_MILESTONE, "completed"), "open_children"),
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
            {"kind": "reassign", "row": 1, "item_type": "task", "item_id": str(_GMAIL_TASK), "owner": "dana"},
            "invalid_owner",
        ),
    ],
)
def test_apply_operations_invalid_operation_refused_with_code(operation: dict[str, JsonValue], code: str) -> None:
    result = apply_operations(_graph(), _request(operation), _ids(), _NOW)

    assert not result.ok
    assert code in result.message


def test_apply_operations_completed_with_open_blocker_refused() -> None:
    graph = _graph()
    facts = graph.derived.tasks[_GMAIL_TASK]
    all_done = dataclasses.replace(facts, dod=dataclasses.replace(facts.dod, done=facts.dod.total))
    tasks = {**graph.derived.tasks, _GMAIL_TASK: all_done}
    graph = dataclasses.replace(graph, derived=dataclasses.replace(graph.derived, tasks=tasks))

    result = apply_operations(graph, _request(_status("task", _GMAIL_TASK, "completed")), _ids(), _NOW)

    assert not result.ok
    assert "open_blockers" in result.message


def test_apply_operations_milestone_with_dispositions_completes() -> None:
    graph = _graph()
    children = [str(t) for t, task in graph.records.tasks.items() if task.milestone_id == _CONNECTORS_MILESTONE]
    operation = _status(
        "milestone", _CONNECTORS_MILESTONE, "completed", child_dispositions={c: "moved" for c in children}
    )

    result = apply_operations(graph, _request(operation), _ids(), _NOW)

    assert result.ok
    assert result.value.graph.records.milestones[_CONNECTORS_MILESTONE].state == "completed"


def test_apply_operations_spec_request_invalid_operation_applies_nothing() -> None:
    request = TypeAdapter(Operations).validate_python(load_spec("operations.json"))

    result = apply_operations(_graph(), request, _ids(), _NOW)

    assert not result.ok
    assert result.message.startswith("operation[3] unplan: unknown_record")
