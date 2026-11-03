# Responsibility: Build the point-in-time state graph from the records every source returned.
# Public interface:
# `-- build_state_graph(project_reads, plan_reads, settings, built_at)
"""Functional core of `collect_current_state`: context -> records -> tree -> index -> derived -> diagnostics."""

from collections.abc import Sequence
from datetime import UTC, datetime, timedelta

from nyssa_ai_result import Err, Result, fail, ok

from daily_tasks.domain import Diagnostic, RecordSourceStatus, StateGraph, StateGraphContext, StateGraphDerived
from daily_tasks.graph.build_index import build_index
from daily_tasks.graph.build_record_nodes import build_record_nodes
from daily_tasks.graph.build_tree import build_tree
from daily_tasks.graph.derive_blocker_facts import derive_blocker_facts
from daily_tasks.graph.derive_milestone_facts import derive_milestone_facts
from daily_tasks.graph.derive_rollover import derive_rollover
from daily_tasks.graph.derive_summary import derive_summary
from daily_tasks.graph.derive_task_facts import derive_task_facts
from daily_tasks.graph.derive_today import derive_today
from daily_tasks.graph.inventory_hash import inventory_hash
from daily_tasks.graph.local_date_in import local_date_in
from daily_tasks.graph.merge_records import merge_records
from daily_tasks.graph.resolve_relations import resolve_relations
from daily_tasks.graph.types import DailyPlanSourceRead, ProjectPlanSourceRead, StateGraphSettings


def build_state_graph(
    project_reads: Sequence[ProjectPlanSourceRead],
    plan_reads: Sequence[DailyPlanSourceRead],
    settings: StateGraphSettings,
    built_at: datetime,
) -> Result[StateGraph]:
    """Return the graph for the local date of `built_at` in `settings.timezone`.

    A failed source is reported in `context.sources` and as an error diagnostic; the graph is built from
    the sources that were read. Fails with `Validation` when `built_at` is not UTC or the timezone is
    unknown, and with `Unavailable` when project-plan sources are configured but none could be read.
    """
    if built_at.utcoffset() != timedelta(0):
        return fail("Build time must be UTC.", "Validation")
    local_date = local_date_in(built_at, settings.timezone)
    if isinstance(local_date, Err):
        return local_date
    snapshots = [read.snapshot for read in project_reads if read.snapshot is not None]
    if project_reads and not snapshots:
        return fail("No project-plan source could be read.", "Unavailable")
    records, merge_diagnostics = merge_records(snapshots, [plan for read in plan_reads for plan in read.plans])
    relations = resolve_relations(records)
    tree, tree_diagnostics = build_tree(records)
    index = build_index(records, relations, tree, settings)
    milestone_facts = derive_milestone_facts(records, relations, tree)
    plannable = {key for key, facts in milestone_facts.items() if facts.lowest_incomplete}
    task_facts = derive_task_facts(records, relations, plannable, settings.user.email, local_date.value)
    rollover = derive_rollover(records, local_date.value)
    today = derive_today(records, task_facts, local_date.value)
    context = StateGraphContext(
        workspace_root=settings.workspace_root,
        projects_root=settings.projects_root,
        daily_plans_root=settings.daily_plans_root,
        user=settings.user,
        timezone=settings.timezone,
        local_date=local_date.value,
        built_at=built_at.astimezone(UTC),
        inventory_hash=inventory_hash(records, index.file_hashes),
        sources=_source_statuses(project_reads, plan_reads),
    )
    derived = StateGraphDerived(
        tasks=task_facts,
        blockers=derive_blocker_facts(records, local_date.value),
        milestones=milestone_facts,
        rollover=rollover,
        today=today,
        summary=derive_summary(records, task_facts, today, rollover, settings),
    )
    diagnostics = (
        *_source_diagnostics(project_reads, plan_reads),
        *merge_diagnostics,
        *relations.diagnostics,
        *tree_diagnostics,
    )
    graph = StateGraph(
        context=context,
        records=build_record_nodes(records),
        tree=tree,
        index=index,
        derived=derived,
        diagnostics=diagnostics,
    )
    return ok(graph)


def _source_statuses(
    project_reads: Sequence[ProjectPlanSourceRead], plan_reads: Sequence[DailyPlanSourceRead]
) -> tuple[RecordSourceStatus, ...]:
    statuses: list[RecordSourceStatus] = []
    for project_read in project_reads:
        snapshot = project_read.snapshot
        count = (
            0
            if snapshot is None
            else len(snapshot.projects) + len(snapshot.milestones) + len(snapshot.tasks) + len(snapshot.blockers)
        )
        statuses.append(_status("project-plan", project_read.name, count, project_read.error, snapshot is None))
    for plan_read in plan_reads:
        failed = plan_read.error is not None
        statuses.append(_status("daily-plan", plan_read.name, len(plan_read.plans), plan_read.error, failed))
    return tuple(statuses)


def _status(port: str, name: str, count: int, error: str | None, failed: bool) -> RecordSourceStatus:
    return RecordSourceStatus(
        port=port, name=name, status="error" if failed else "ok", record_count=count, error=error if failed else None
    )


def _source_diagnostics(
    project_reads: Sequence[ProjectPlanSourceRead], plan_reads: Sequence[DailyPlanSourceRead]
) -> list[Diagnostic]:
    failed = [(read.name, read.error) for read in project_reads if read.snapshot is None]
    failed += [(read.name, read.error) for read in plan_reads if read.error is not None]
    return [
        Diagnostic(level="error", code="SOURCE_UNAVAILABLE", source=name, detail=error or "source could not be read.")
        for name, error in failed
    ]
