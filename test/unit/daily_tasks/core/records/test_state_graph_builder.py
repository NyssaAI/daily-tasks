"""Responsibility: Prove StateGraphBuilder reads every configured repository concurrently and logs one outcome.
Public interface:
+-- test_state_graph_builder_all_project_sources_failing_logs_error(log_capture)
+-- test_state_graph_builder_failing_source_is_reported_and_warned(log_capture)
`-- test_state_graph_builder_sources_are_read_concurrently_and_merged(log_capture)

State graph build through fake ProjectPlanRepository and DailyPlanRepository collaborators.
"""

import asyncio
from dataclasses import dataclass, field
from datetime import date, datetime

from nyssa_ai_result import Err, Ok, Result, fail, ok
from state_graph_records import BUILT_AT, SETTINGS, milestone, plan, project, record_id, task

from conftest import LogCapture
from daily_tasks.core.records import DailyPlan, ProjectPlanSnapshot, StateGraphBuilder


@dataclass
class _ProjectRepo:
    name: str
    snapshot: ProjectPlanSnapshot | None
    started: asyncio.Event = field(default_factory=asyncio.Event)
    peer: asyncio.Event | None = None

    async def fetch_projects(self) -> Result[ProjectPlanSnapshot]:
        self.started.set()
        if self.peer is not None:
            await asyncio.wait_for(self.peer.wait(), timeout=1)
        return fail("projects root unreadable", "Unavailable") if self.snapshot is None else ok(self.snapshot)


@dataclass
class _PlanRepo:
    name: str
    plans: tuple[DailyPlan, ...]
    requested: list[date] = field(default_factory=list)

    async def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        self.requested.append(around)
        return ok(self.plans)


def _snapshot(project_number: int, milestone_number: int, task_number: int) -> ProjectPlanSnapshot:
    return ProjectPlanSnapshot(
        projects=(project(project_number, f"Project {project_number}"),),
        milestones=(milestone(milestone_number, "Build", project_id=project_number),),
        tasks=(task(task_number, milestone_number, f"Task {task_number}"),),
        blockers=(),
    )


def _clock() -> datetime:
    return BUILT_AT


def test_state_graph_builder_sources_are_read_concurrently_and_merged(log_capture: LogCapture) -> None:
    first = _ProjectRepo("first", _snapshot(1, 2, 3))
    second = _ProjectRepo("second", _snapshot(11, 12, 13), peer=first.started)
    first.peer = second.started
    plans = _PlanRepo("plans", (plan(date(2026, 11, 3), ()),))
    builder = StateGraphBuilder([first, second], [plans], SETTINGS, _clock)

    result = asyncio.run(builder.build())

    assert isinstance(result, Ok)
    assert set(result.value.records.tasks) == {record_id(3), record_id(13)}
    assert plans.requested == [date(2026, 11, 3)]
    level, message, fields = log_capture.records[-1]
    assert (level, message, fields["tasks"], fields["failed_sources"]) == ("info", "state graph built", 2, [])
    assert isinstance(fields["elapsed_ms"], float)


def test_state_graph_builder_failing_source_is_reported_and_warned(log_capture: LogCapture) -> None:
    healthy = _ProjectRepo("healthy", _snapshot(1, 2, 3))
    broken = _ProjectRepo("broken", None)

    result = asyncio.run(StateGraphBuilder([healthy, broken], [], SETTINGS, _clock).build())

    assert isinstance(result, Ok)
    assert [(s.name, s.status) for s in result.value.context.sources] == [("healthy", "ok"), ("broken", "error")]
    assert log_capture.records[-1][0] == "warn"
    assert log_capture.records[-1][2]["failed_sources"] == ["broken"]


def test_state_graph_builder_all_project_sources_failing_logs_error(log_capture: LogCapture) -> None:
    result = asyncio.run(StateGraphBuilder([_ProjectRepo("broken", None)], [], SETTINGS, _clock).build())

    assert isinstance(result, Err)
    assert result.category == "Unavailable"
    assert [(level, fields["category"]) for level, _, fields in log_capture.records] == [("error", "Unavailable")]
