# Responsibility: Merge the records of every source into one id-keyed record set.
# Public interface:
# `-- merge_records(snapshots, plans)
"""Source records keyed by id; duplicates are kept once and reported as diagnostics."""

from collections.abc import Sequence
from datetime import date
from uuid import UUID

from daily_tasks.domain import Blocker, DailyPlan, Diagnostic, Milestone, Project, Task
from daily_tasks.graph.types import GraphRecords
from daily_tasks.ports import ProjectPlanSnapshot

type _Record = Project | Milestone | Task | Blocker


def merge_records(
    snapshots: Sequence[ProjectPlanSnapshot], plans: Sequence[DailyPlan]
) -> tuple[GraphRecords, tuple[Diagnostic, ...]]:
    """Key records by id in source order; the first record with an id (or plan with a date) wins.

    Ids are unique across record kinds, so a task reusing a project id is a duplicate too.
    """
    seen: dict[UUID, _Record] = {}
    diagnostics: list[Diagnostic] = []
    projects: dict[UUID, Project] = {}
    milestones: dict[UUID, Milestone] = {}
    tasks: dict[UUID, Task] = {}
    blockers: dict[UUID, Blocker] = {}
    for snapshot in snapshots:
        _add_all(snapshot.projects, projects, seen, diagnostics)
        _add_all(snapshot.milestones, milestones, seen, diagnostics)
        _add_all(snapshot.tasks, tasks, seen, diagnostics)
        _add_all(snapshot.blockers, blockers, seen, diagnostics)
    by_date: dict[date, DailyPlan] = {}
    for plan in plans:
        kept = by_date.get(plan.local_date)
        if kept is None:
            by_date[plan.local_date] = plan
        elif kept.id != plan.id:
            diagnostics.append(
                _duplicate(plan.path, f"daily plan for {plan.local_date} already read from {kept.path}.")
            )
    ordered_plans = {day: by_date[day] for day in sorted(by_date)}
    records = GraphRecords(
        projects=projects, milestones=milestones, tasks=tasks, blockers=blockers, plans=ordered_plans
    )
    return records, tuple(diagnostics)


def _add_all[R: _Record](
    incoming: Sequence[R], target: dict[UUID, R], seen: dict[UUID, _Record], diagnostics: list[Diagnostic]
) -> None:
    for record in incoming:
        kept = seen.get(record.id)
        if kept is None:
            seen[record.id] = record
            target[record.id] = record
        elif kept != record:
            diagnostics.append(_duplicate(record.path, f"id {record.id} already read from {_location(kept)}."))


def _location(record: _Record) -> str:
    return f"{record.path} ({record.source})"


def _duplicate(path: str, detail: str) -> Diagnostic:
    return Diagnostic(level="warning", code="DUPLICATE_ID", path=path, detail=detail)
