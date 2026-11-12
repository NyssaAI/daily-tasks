"""Responsibility: Prove suggestion verdicts are validated, applied, pruned, and logged explicitly.
Public interface:
+-- test_adjudicate_suggestions_accept_blocker_resolve_resolves_blocker()
+-- test_adjudicate_suggestions_accept_status_prunes_logs_and_stages_change()
+-- test_adjudicate_suggestions_dod_then_complete_task_succeeds()
+-- test_adjudicate_suggestions_edit_applies_edited_state()
+-- test_adjudicate_suggestions_invalid_verdicts_refused(verdicts, code)
+-- test_adjudicate_suggestions_no_verdicts_keeps_everything_pending()
`-- test_adjudicate_suggestions_reject_logs_without_record_change()

Suggestion adjudication tests against the `docs/specs` state graph and suggestions examples.
"""

from collections.abc import Callable, Iterator
from datetime import UTC, datetime
from itertools import count
from typing import Literal
from uuid import UUID

import pytest
from pydantic import JsonValue, TypeAdapter

from conftest import load_spec
from daily_tasks.core.communications import Suggestions
from daily_tasks.core.planning import (
    Actor,
    AdjudicationVerdict,
    Operations,
    adjudicate_suggestions,
    apply_operations,
)
from daily_tasks.core.records import StateGraph

_NOW = datetime(2026, 11, 3, 14, 24, tzinfo=UTC)
_ACTOR = Actor(kind="person", id="jordan@example.com")
_SESSION = UUID("019a4b2c-9000-7000-8000-0000000000a1")
_FETCH_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000004")
_REVIEW_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000008")
_STATUS_SUGGESTION = UUID("019a4b2c-9000-7000-8000-0000000000b4")
_BLOCKER_SUGGESTION = UUID("019a4b2c-9000-7000-8000-0000000000b5")


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
            "session_id": str(_SESSION),
            "screen_id": "s2",
            "original_words": "words",
            "actor": {"kind": "person", "id": "jordan@example.com"},
            "operations": list(operations),
        }
    )


def _status(record_kind: str, record_id: UUID, state: str) -> dict[str, JsonValue]:
    return {
        "kind": "set-status",
        "row": 1,
        "record_kind": record_kind,
        "record_id": str(record_id),
        "state": state,
        "activity_at": "2026-11-03T14:24:00Z",
    }


def _verdict(
    suggestion_id: UUID, verdict: Literal["accept", "edit", "reject"], edits: dict[str, JsonValue] | None = None
) -> AdjudicationVerdict:
    return AdjudicationVerdict(
        suggestion_id=suggestion_id, verdict=verdict, screen_id="s1", row=4, original_words=f"4 {verdict}", edits=edits
    )


def test_adjudicate_suggestions_accept_status_prunes_logs_and_stages_change() -> None:
    result = adjudicate_suggestions(
        _suggestions(), [_verdict(_STATUS_SUGGESTION, "accept")], _graph(), _ACTOR, _SESSION, _NOW, _ids()
    )

    assert result.ok
    assert [s.id for s in result.value.suggestions.suggestions] == [_BLOCKER_SUGGESTION]
    assert result.value.suggestions.updated_at == _NOW
    assert result.value.graph.records.tasks[_FETCH_TASK].state == "in-progress"
    (entry,) = result.value.decisions
    assert (entry.verdict, entry.action, entry.origin.kind) == ("accept", "set-status", "suggestion")
    (change,) = result.value.changes
    assert change.origin.suggestion_id == _STATUS_SUGGESTION and change.after == {"state": "in-progress"}


def test_adjudicate_suggestions_reject_logs_without_record_change() -> None:
    result = adjudicate_suggestions(
        _suggestions(), [_verdict(_BLOCKER_SUGGESTION, "reject")], _graph(), _ACTOR, _SESSION, _NOW, _ids()
    )

    assert result.ok
    assert [s.id for s in result.value.suggestions.suggestions] == [_STATUS_SUGGESTION]
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
        _suggestions(), [_verdict(_BLOCKER_SUGGESTION, "accept")], _graph(), _ACTOR, _SESSION, _NOW, _ids()
    )

    assert result.ok
    assert result.value.graph.records.blockers[UUID("019a4b2c-1f00-7a10-8000-000000000016")].state == "resolved"
    assert result.value.decisions[0].action == "resolve-blocker"


def test_adjudicate_suggestions_edit_applies_edited_state() -> None:
    edits: dict[str, JsonValue] = {"state": "cancelled"}

    result = adjudicate_suggestions(
        _suggestions(), [_verdict(_STATUS_SUGGESTION, "edit", edits)], _graph(), _ACTOR, _SESSION, _NOW, _ids()
    )

    assert result.ok
    assert result.value.graph.records.tasks[_FETCH_TASK].state == "cancelled"
    assert result.value.decisions[0].edits == edits


def test_adjudicate_suggestions_no_verdicts_keeps_everything_pending() -> None:
    suggestions = _suggestions()

    result = adjudicate_suggestions(suggestions, [], _graph(), _ACTOR, _SESSION, _NOW, _ids())

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
                    "created_in_session": str(_SESSION),
                    "source_message_ids": ["gmail:1"],
                    "evidence": "review done",
                    "rationale": "The review is done.",
                    "target": {
                        "record_kind": "task",
                        "record_id": str(_REVIEW_TASK),
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

    adjudicated = adjudicate_suggestions(suggestion, [verdict], _graph(), _ACTOR, _SESSION, _NOW, _ids())
    assert adjudicated.ok
    completed = apply_operations(
        adjudicated.value.graph, _request(_status("task", _REVIEW_TASK, "completed")), _ids(), _NOW
    )

    assert adjudicated.value.decisions[0].action == "check-dod"
    assert adjudicated.value.suggestions.suggestions == ()
    assert completed.ok


def _suggestion_pool() -> dict[str, JsonValue]:
    return {"vault_root": "D:/vaults/work", "updated_at": "2026-11-03T14:20:05Z", "no_suggestion_message_ids": []}


@pytest.mark.parametrize(
    ("verdicts", "code"),
    [
        ([_verdict(UUID("019a4b2c-9000-7000-8000-0000000000ff"), "accept")], "unknown_suggestion"),
        ([_verdict(_STATUS_SUGGESTION, "reject"), _verdict(_STATUS_SUGGESTION, "accept")], "duplicate_verdict"),
        ([_verdict(_STATUS_SUGGESTION, "edit")], "invalid_edits"),
    ],
)
def test_adjudicate_suggestions_invalid_verdicts_refused(verdicts: list[AdjudicationVerdict], code: str) -> None:
    result = adjudicate_suggestions(_suggestions(), verdicts, _graph(), _ACTOR, _SESSION, _NOW, _ids())

    assert not result.ok
    assert code in result.message
