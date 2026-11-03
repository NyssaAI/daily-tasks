# Responsibility: Prove today's selection follows the planned days operations set.
# Public interface:
# (none)
"""`refresh_today` after assign-to-day and unplan operations on the spec state graph."""

from datetime import date
from uuid import UUID

from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import PlanItem, StateGraph
from daily_tasks.session.operation_planned_for import operation_planned_for
from daily_tasks.session.refresh_today import refresh_today

TODAY = date(2026, 11, 3)


def _graph() -> StateGraph:
    return TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))


def _selected(graph: StateGraph) -> set[UUID]:
    selected = graph.derived.today.selected
    return {item.item_id for item in (*selected.mine, *selected.delegated, *selected.follow_up)}


def test_refresh_today_assigned_task_joins_selection() -> None:
    graph = _graph()
    task_id = graph.derived.today.available[0]
    planned = operation_planned_for(graph, "task", task_id, TODAY)
    assert planned.ok

    refreshed = refresh_today(planned.value[0])

    assert task_id in _selected(refreshed)
    assert task_id not in refreshed.derived.today.available
    assert refreshed.derived.summary.selected_today == len(_selected(refreshed))


def test_refresh_today_unplanned_task_leaves_selection() -> None:
    graph = _graph()
    item: PlanItem = next(i for i in graph.derived.today.selected.delegated if i.item_type == "task")
    unplanned = operation_planned_for(graph, "task", item.item_id, None)
    assert unplanned.ok

    refreshed = refresh_today(unplanned.value[0])

    assert item.item_id not in _selected(refreshed)
