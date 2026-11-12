"""Responsibility: Prove the planning session lifecycle moves through its screens with stable row numbers.
Public interface:
+-- NOW
+-- PROJECT_1
+-- PROJECT_2
+-- SESSION_ID
+-- test_add_suggestions_later_keeps_existing_numbers()
+-- test_add_suggestions_twice_does_not_duplicate_rows()
+-- test_cancel_session_from_running_stage_is_terminal(stage)
+-- test_confirm_session_stamps_confirmed_at_and_keeps_suggestions_pending()
+-- test_finish_assign_days_renumbers_confirm_rows_from_one()
+-- test_next_project_takes_next_free_numbers_and_last_project_refuses()
+-- test_resolve_row_number_from_another_screen_is_refused()
+-- test_review_projects_continues_session_numbering_with_labels()
+-- test_session_snapshot_round_trips_as_planning_session()
+-- test_start_session_numbers_plan_then_pending_suggestions()
+-- test_start_session_previous_plan_carries_open_tasks_forward()
+-- test_start_session_twice_returns_conflict()
`-- test_transition_from_wrong_stage_returns_conflict_naming_next_step(stage, transition, expected_hint)

Planning session transitions, numbering rules, row resolution and snapshot parity.
"""

import dataclasses
from collections.abc import Mapping
from datetime import UTC, datetime
from uuid import UUID

import pytest
from nyssa_ai_result import Err, Ok, Result
from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.core.communications import Suggestions
from daily_tasks.core.planning import (
    PlanningSession,
    RowRef,
    SessionStage,
    SessionState,
    add_suggestions,
    cancel_session,
    confirm_session,
    finish_assign_days,
    next_project,
    resolve_row,
    review_projects,
    start_session,
)
from daily_tasks.core.records import DailyPlan, StateGraph

NOW = datetime(2026, 11, 3, 14, 2, tzinfo=UTC)
SESSION_ID = UUID("019a4b2c-9000-7000-8000-0000000000a1")
PROJECT_1 = UUID("019a4b2c-1f00-7a10-8000-000000000001")
PROJECT_2 = UUID("019a4b2c-1f00-7a10-8000-000000000011")


def _id(suffix: str) -> UUID:
    return UUID(f"019a4b2c-1f00-7a10-8000-000000000{suffix}")


def _task(suffix: str) -> RowRef:
    return RowRef(kind="task", id=_id(suffix))


def _suggestions() -> Suggestions:
    return TypeAdapter(Suggestions).validate_python(load_spec("suggestions.json"))


def _initial(with_suggestions: bool = True) -> SessionState:
    graph = TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))
    suggestions = _suggestions().suggestions if with_suggestions else ()
    return SessionState.initial(
        state_graph=graph,
        suggestions=suggestions,
        session_id=SESSION_ID,
        vault_root="D:/vaults/work",
        suggestions_file="suggestions.json",
        focus=None,
        now=NOW,
    )


def _value(result: Result[SessionState]) -> SessionState:
    assert isinstance(result, Ok), result
    return result.value


def _rows(state: SessionState, key: str) -> dict[int, RowRef]:
    rows = state.session.screens[key].rows
    assert isinstance(rows, Mapping)
    return dict(rows)


def test_start_session_numbers_plan_then_pending_suggestions() -> None:
    state = _value(start_session(_initial(), None, NOW))

    assert state.stage is SessionStage.SCREEN_1
    assert state.session.current_screen == "s1"
    assert _rows(state, "s1") == {
        1: _task("003"),
        2: _task("004"),
        3: RowRef(kind="suggestion", id=_suggestions().suggestions[0].id),
        4: RowRef(kind="suggestion", id=_suggestions().suggestions[1].id),
    }
    assert state.session.next_row == 5
    assert len(state.suggestions) == 2


def test_start_session_previous_plan_carries_open_tasks_forward() -> None:
    previous = TypeAdapter(DailyPlan).validate_python(load_spec("daily-plan.json"))

    state = _value(start_session(_initial(with_suggestions=False), previous, NOW))

    assert list(_rows(state, "s1").values()) == [_task("003"), _task("004"), _task("008")]


def test_add_suggestions_later_keeps_existing_numbers() -> None:
    started = _value(start_session(_initial(with_suggestions=False), None, NOW))
    before = _rows(started, "s1")

    state = _value(add_suggestions(started, _suggestions().suggestions, NOW))

    rows = _rows(state, "s1")
    assert {n: rows[n] for n in before} == before
    assert [rows[3].kind, rows[4].kind] == ["suggestion", "suggestion"]
    assert state.session.next_row == 5


def test_add_suggestions_twice_does_not_duplicate_rows() -> None:
    started = _value(start_session(_initial(), None, NOW))

    state = _value(add_suggestions(started, _suggestions().suggestions, NOW))

    assert _rows(state, "s1") == _rows(started, "s1")
    assert len(state.suggestions) == 2


def test_review_projects_continues_session_numbering_with_labels() -> None:
    state = _value(review_projects(_value(start_session(_initial(), None, NOW)), NOW))

    assert state.stage is SessionStage.SCREEN_2
    assert state.session.current_screen == f"s2:{PROJECT_1}"
    rows = _rows(state, f"s2:{PROJECT_1}")
    assert min(rows) == 5
    assert rows[5] == _task("003")
    assert rows[12] == RowRef(kind="blocker", id=_id("005"))
    assert state.session.labels[PROJECT_1]["M2"] == _id("002")
    assert _value_ref(resolve_row(state.session, "M3")) == RowRef(kind="milestone", id=_id("012"))


def _value_ref(result: Result[RowRef]) -> RowRef:
    assert isinstance(result, Ok), result
    return result.value


def test_next_project_takes_next_free_numbers_and_last_project_refuses() -> None:
    first = _value(review_projects(_value(start_session(_initial(), None, NOW)), NOW))

    second = _value(next_project(first, NOW))

    assert second.session.assign_days.current_project_id == PROJECT_2
    assert _rows(second, f"s2:{PROJECT_2}") == {13: _task("015"), 14: RowRef(kind="blocker", id=_id("016"))}
    refused = next_project(second, NOW)
    assert isinstance(refused, Err)
    assert "finish" in refused.message


def test_resolve_row_number_from_another_screen_is_refused() -> None:
    state = _value(review_projects(_value(start_session(_initial(), None, NOW)), NOW))

    refused = resolve_row(state.session, "1")

    assert isinstance(refused, Err)
    assert refused.category == "Conflict"
    assert _value_ref(resolve_row(state.session, "#6")) == _task("004")


def test_finish_assign_days_renumbers_confirm_rows_from_one() -> None:
    on_s2 = _value(review_projects(_value(start_session(_initial(), None, NOW)), NOW))

    state = _value(finish_assign_days(on_s2, NOW))

    assert state.stage is SessionStage.SCREEN_3
    assert _rows(state, "s3") == {
        1: _task("008"),
        2: _task("003"),
        3: _task("004"),
        4: RowRef(kind="blocker", id=_id("005")),
    }
    assert state.session.screens["s3"].numbering == "screen"
    assert _value_ref(resolve_row(state.session, "1")) == _task("008")
    assert isinstance(resolve_row(state.session, "12"), Err)
    assert state.session.next_row == on_s2.session.next_row


def test_confirm_session_stamps_confirmed_at_and_keeps_suggestions_pending() -> None:
    later = datetime(2026, 11, 3, 14, 30, tzinfo=UTC)
    on_s3 = _value(finish_assign_days(_value(review_projects(_value(start_session(_initial(), None, NOW)), NOW)), NOW))

    state = _value(confirm_session(on_s3, later))

    assert state.stage is SessionStage.CONFIRMED
    assert state.session.confirmed_at == later
    assert state.suggestions == on_s3.suggestions


@pytest.mark.parametrize(
    ("stage", "transition", "expected_hint"),
    [
        (SessionStage.INIT, review_projects, "start the session"),
        (SessionStage.INIT, confirm_session, "finish"),
        (SessionStage.SCREEN_1, finish_assign_days, "yes"),
        (SessionStage.SCREEN_1, next_project, "yes"),
        (SessionStage.CONFIRMED, cancel_session, "start a new one"),
        (SessionStage.CANCELLED, review_projects, "start a new one"),
    ],
)
def test_transition_from_wrong_stage_returns_conflict_naming_next_step(
    stage: SessionStage, transition: object, expected_hint: str
) -> None:
    state = dataclasses.replace(_initial(), stage=stage)
    assert callable(transition)

    result = transition(state, NOW)

    assert isinstance(result, Err)
    assert result.category == "Conflict"
    assert expected_hint in result.message


def test_start_session_twice_returns_conflict() -> None:
    started = _value(start_session(_initial(), None, NOW))

    assert isinstance(start_session(started, None, NOW), Err)


@pytest.mark.parametrize(
    "stage", [SessionStage.INIT, SessionStage.SCREEN_1, SessionStage.SCREEN_2, SessionStage.SCREEN_3]
)
def test_cancel_session_from_running_stage_is_terminal(stage: SessionStage) -> None:
    state = _value(cancel_session(dataclasses.replace(_initial(), stage=stage), NOW))

    assert state.stage is SessionStage.CANCELLED
    assert isinstance(add_suggestions(state, (), NOW), Err)


def test_session_snapshot_round_trips_as_planning_session() -> None:
    state = _value(next_project(_value(review_projects(_value(start_session(_initial(), None, NOW)), NOW)), NOW))
    adapter = TypeAdapter(PlanningSession)
    spec = load_spec("planning-session.json")
    assert isinstance(spec, dict)
    spec_keys = set(spec) - {"_note", "_rules"}

    dumped = adapter.dump_python(state.session, mode="json", exclude_unset=False)

    assert set(dumped) == spec_keys
    assert adapter.validate_python(dumped) == state.session
