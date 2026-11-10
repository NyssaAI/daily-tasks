"""Responsibility: Prove build_state_graph indexes, nests and derives facts from hand-built records.
Public interface:
+-- DANA
+-- SARAH
+-- test_build_state_graph_blocker_and_milestone_facts_report_progress()
+-- test_build_state_graph_failed_source_is_reported_not_fatal()
+-- test_build_state_graph_inventory_hash_ignores_source_order()
+-- test_build_state_graph_json_round_trips_with_the_spec_key_structure()
+-- test_build_state_graph_local_date_follows_timezone()
+-- test_build_state_graph_lookups_cover_paths_people_terms_and_hashes()
+-- test_build_state_graph_no_readable_project_source_fails_unavailable()
+-- test_build_state_graph_non_utc_build_time_fails_validation()
+-- test_build_state_graph_records_are_indexed_by_uuid7_id()
+-- test_build_state_graph_relations_are_indexed_in_both_directions()
+-- test_build_state_graph_rollover_carries_reselected_and_drops_the_rest()
+-- test_build_state_graph_task_facts_flag_late_blocked_and_delegated_work()
+-- test_build_state_graph_today_and_summary_count_open_work()
+-- test_build_state_graph_tree_nests_projects_by_directory_date()
+-- test_build_state_graph_unknown_refs_and_duplicates_become_diagnostics()
`-- test_build_state_graph_without_todays_plan_proposes_rollover_as_due()

Pure state graph build: records, tree, index, derived facts, diagnostics and JSON shape.
"""

from datetime import UTC, date, datetime

from nyssa_ai_result import Err, Ok
from pydantic import JsonValue, TypeAdapter
from state_graph_records import BUILT_AT, SETTINGS, USER, blocker, milestone, plan, project, record_id, task

from conftest import load_spec
from daily_tasks.domain import DailyPlan, DailyPlanEntry, ItemType, PlanItem, StateGraph
from daily_tasks.graph import (
    DailyPlanSourceRead,
    ProjectPlanSourceRead,
    build_state_graph,
    dod_ratio,
    format_dod_progress,
    milestone_completion_percent,
)
from daily_tasks.ports import ProjectPlanSnapshot

SARAH = "sarah@example.com"
DANA = "dana@example.com"
_STATE_GRAPH: TypeAdapter[StateGraph] = TypeAdapter(StateGraph)


def _snapshot() -> ProjectPlanSnapshot:
    return ProjectPlanSnapshot(
        projects=(project(11, "Cloud Sync", date(2026, 10, 25)), project(1, "Daily Tasks MCP Server")),
        milestones=(
            milestone(16, "Design", "completed"),
            milestone(2, "Planning session spike", done=(True, True)),
            milestone(12, "Connectors"),
            milestone(13, "Auth", project_id=11),
        ),
        tasks=(
            task(30, 16, "Architecture spike", "completed", done=(True,)),
            task(
                3,
                2,
                "Wire Gmail connector",
                "in-progress",
                assignee=SARAH,
                target_date=date(2026, 11, 5),
                done=(True, False),
                blocked_by=(5,),
            ),
            task(4, 2, "Background fetch survives turns", depends_on=(3,)),
            task(7, 2, "Draft connector README", target_date=date(2026, 11, 2), done=(True,)),
            task(8, 2, "Dropped idea", "cancelled"),
            task(14, 12, "Slack connector", owner=DANA),
        ),
        blockers=(blocker(5, "Google OAuth app verification", blocks=(7,)), blocker(17, "Vendor contract", (), 11)),
    )


def _entry(item_id: int, section: str = "my-work", item_type: ItemType = "task") -> DailyPlanEntry:
    return TypeAdapter(DailyPlanEntry).validate_python(
        {
            "item_type": item_type,
            "item_id": str(record_id(item_id)),
            "section": section,
            "carried_from": None,
            "added_at": "2026-11-03T14:05:00Z",
        }
    )


def _plans() -> tuple[DailyPlan, ...]:
    return (
        plan(date(2026, 11, 3), (_entry(3, "delegated-work"), _entry(5, item_type="blocker"))),
        plan(date(2026, 11, 2), (_entry(3, "delegated-work"), _entry(7), _entry(30))),
        plan(date(2026, 11, 5), (_entry(4, "delegated-work"),)),
    )


def _build(plans: tuple[DailyPlan, ...] | None = None) -> StateGraph:
    result = build_state_graph(
        [ProjectPlanSourceRead(name="markdown-projects", snapshot=_snapshot())],
        [DailyPlanSourceRead(name="markdown-daily-plans", plans=_plans() if plans is None else plans)],
        SETTINGS,
        BUILT_AT,
    )
    assert isinstance(result, Ok)
    return result.value


def test_build_state_graph_records_are_indexed_by_uuid7_id() -> None:
    graph = _build()

    assert graph.records.tasks[record_id(3)].title == "Wire Gmail connector"
    assert graph.records.blockers[record_id(5)].owner == USER
    assert list(graph.records.plans) == [date(2026, 11, 2), date(2026, 11, 3), date(2026, 11, 5)]
    assert graph.records.plans[date(2026, 11, 2)].completed_ids == (record_id(30),)
    assert graph.context.local_date == date(2026, 11, 3)


def test_build_state_graph_tree_nests_projects_by_directory_date() -> None:
    graph = _build()

    assert [node.project_id for node in graph.tree] == [record_id(1), record_id(11)]
    first = graph.tree[0]
    assert [m.milestone_id for m in first.milestones] == [record_id(2), record_id(12), record_id(16)]
    assert first.milestones[0].task_ids == (record_id(3), record_id(4), record_id(7), record_id(8))
    assert first.blocker_ids == (record_id(5),)
    assert graph.index.project_order == (record_id(1), record_id(11))


def test_build_state_graph_relations_are_indexed_in_both_directions() -> None:
    index = _build().index

    assert index.parent[record_id(3)] == record_id(2)
    assert index.parent[record_id(5)] == record_id(1)
    assert index.depends_on == {record_id(4): (record_id(3),)}
    assert index.required_by == {record_id(3): (record_id(4),)}
    assert index.blocked_by[record_id(3)] == (record_id(5),)
    assert index.blocked_by[record_id(7)] == (record_id(5),)
    assert index.blocks == {record_id(5): (record_id(3), record_id(7))}


def test_build_state_graph_lookups_cover_paths_people_terms_and_hashes() -> None:
    index = _build().index

    assert index.by_path["p1/m2/t3.md"] == record_id(3)
    assert index.by_person[SARAH].assigned == (record_id(3),)
    assert record_id(14) in index.by_person[DANA].owns
    assert index.title_terms["connector"] == (record_id(3), record_id(7), record_id(14))
    assert index.title_terms["oauth"] == (record_id(5),)
    assert index.file_hashes["daily-plans/2026.11.03-daily-plan.md"] == "sha256:20261103"
    assert index.threads == {}


def test_build_state_graph_task_facts_flag_late_blocked_and_delegated_work() -> None:
    tasks = _build().derived.tasks

    assert record_id(30) not in tasks and record_id(8) not in tasks
    gmail = tasks[record_id(3)]
    assert (gmail.responsibility, gmail.blocked, gmail.late) == ("delegated", True, False)
    assert gmail.planned_for == date(2026, 11, 3)
    assert format_dod_progress(gmail.dod) == "1/2" and dod_ratio(gmail.dod) == 0.5
    readme = tasks[record_id(7)]
    assert (readme.late, readme.blocked, readme.closable, readme.planned_for) == (True, True, False, None)
    assert tasks[record_id(4)].waiting_on == (record_id(3),)
    assert tasks[record_id(4)].planned_for == date(2026, 11, 5)
    assert tasks[record_id(14)].responsibility == "follow-up"
    assert tasks[record_id(14)].eligible is False


def test_build_state_graph_blocker_and_milestone_facts_report_progress() -> None:
    derived = _build().derived

    assert derived.blockers[record_id(5)].planned_for == date(2026, 11, 3)
    assert derived.blockers[record_id(17)].planned_for is None
    spike = derived.milestones[record_id(2)]
    assert (spike.lowest_incomplete, spike.tasks_open, spike.tasks_total) == (True, 3, 3)
    assert milestone_completion_percent(spike) == 0.0
    assert derived.milestones[record_id(12)].in_progress_plannable is True
    design = derived.milestones[record_id(16)]
    assert (design.lowest_incomplete, design.closable, milestone_completion_percent(design)) == (False, False, 100.0)


def test_build_state_graph_rollover_carries_reselected_and_drops_the_rest() -> None:
    rollover = _build().derived.rollover

    assert (rollover.from_date, rollover.status) == (date(2026, 11, 2), "complete")
    assert rollover.carried == (record_id(3),)
    assert [(d.task_id, d.reason) for d in rollover.dropped] == [(record_id(7), "not reselected; still open and late")]


def test_build_state_graph_without_todays_plan_proposes_rollover_as_due() -> None:
    graph = _build(plans=(plan(date(2026, 11, 2), (_entry(3), _entry(7), _entry(30))),))

    assert graph.derived.rollover.status == "due"
    assert graph.derived.rollover.carried == (record_id(3), record_id(7))
    assert graph.derived.summary.selected_today == 0


def test_build_state_graph_today_and_summary_count_open_work() -> None:
    derived = _build().derived

    assert derived.today.selected.mine == (PlanItem(item_type="blocker", item_id=record_id(5)),)
    assert derived.today.selected.delegated == (PlanItem(item_type="task", item_id=record_id(3)),)
    assert derived.today.available == (record_id(7),)
    assert derived.today.future == {date(2026, 11, 5): (record_id(4),)}
    summary = derived.summary
    assert (summary.open_projects, summary.open_milestones, summary.open_tasks) == (2, 3, 4)
    assert (summary.late_tasks, summary.blocked_tasks, summary.open_blockers) == (1, 2, 2)
    assert (summary.selected_today, summary.carried_forward) == (2, 1)


def test_build_state_graph_unknown_refs_and_duplicates_become_diagnostics() -> None:
    snapshot = _snapshot()
    duplicate_and_orphan = (task(3, 2, "Other copy"), task(40, 99, "Orphan", blocked_by=(98,)))
    extra = ProjectPlanSnapshot(projects=(), milestones=(), tasks=duplicate_and_orphan, blockers=())
    result = build_state_graph(
        [ProjectPlanSourceRead(name="a", snapshot=snapshot), ProjectPlanSourceRead(name="b", snapshot=extra)],
        [],
        SETTINGS,
        BUILT_AT,
    )

    assert isinstance(result, Ok)
    codes = sorted(d.code for d in result.value.diagnostics)
    assert codes == ["DUPLICATE_ID", "ORPHAN_RECORD", "UNRESOLVED_REF"]
    assert result.value.records.tasks[record_id(3)].title == "Wire Gmail connector"


def test_build_state_graph_failed_source_is_reported_not_fatal() -> None:
    result = build_state_graph(
        [ProjectPlanSourceRead(name="markdown-projects", snapshot=_snapshot())],
        [DailyPlanSourceRead(name="markdown-daily-plans", plans=(), error="plans root missing")],
        SETTINGS,
        BUILT_AT,
    )

    assert isinstance(result, Ok)
    status = result.value.context.sources[1]
    assert (status.status, status.error) == ("error", "plans root missing")
    assert result.value.diagnostics[0].code == "SOURCE_UNAVAILABLE"


def test_build_state_graph_no_readable_project_source_fails_unavailable() -> None:
    result = build_state_graph([ProjectPlanSourceRead(name="p", snapshot=None, error="down")], [], SETTINGS, BUILT_AT)

    assert isinstance(result, Err)
    assert result.category == "Unavailable"


def test_build_state_graph_non_utc_build_time_fails_validation() -> None:
    naive = datetime(2026, 11, 3, 14, 0)

    result = build_state_graph([], [], SETTINGS, naive)

    assert isinstance(result, Err)
    assert result.category == "Validation"


def test_build_state_graph_local_date_follows_timezone() -> None:
    late_evening_utc = datetime(2026, 11, 4, 3, 0, tzinfo=UTC)

    result = build_state_graph([ProjectPlanSourceRead(name="p", snapshot=_snapshot())], [], SETTINGS, late_evening_utc)

    assert isinstance(result, Ok)
    assert result.value.context.local_date == date(2026, 11, 3)


def test_build_state_graph_inventory_hash_ignores_source_order() -> None:
    reversed_plans = tuple(reversed(_plans()))

    assert _build().context.inventory_hash == _build(reversed_plans).context.inventory_hash
    assert _build().context.inventory_hash != _build(()).context.inventory_hash


def test_build_state_graph_json_round_trips_with_the_spec_key_structure() -> None:
    graph = _build()

    dumped = _STATE_GRAPH.dump_python(graph, mode="json", by_alias=True)
    reparsed = _STATE_GRAPH.validate_python(dumped)

    assert _STATE_GRAPH.dump_python(reparsed, mode="json", by_alias=True) == dumped
    spec = load_spec("state-graph.json")
    assert isinstance(spec, dict) and isinstance(dumped, dict)
    assert set(dumped) == set(spec) - {"_note"}
    for layer in ("context", "records", "index", "derived"):
        assert set(_dict(dumped[layer])) == set(_dict(spec[layer]))
    assert set(_dict(_dict(dumped["derived"])["summary"])) == set(_dict(_dict(spec["derived"])["summary"]))


def _dict(value: JsonValue) -> dict[str, JsonValue]:
    assert isinstance(value, dict)
    return value
