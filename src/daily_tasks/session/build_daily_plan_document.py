# Responsibility: Build the daily plan document a confirmed planning session writes.
# Public interface:
# `-- build_daily_plan_document(state, decisions, existing, blockers, projects_prefix, plan_id, now)
"""Pure projection of the confirmed selection, staged decisions and blocker records into a `DailyPlanDocument`."""

from collections.abc import Mapping, Sequence
from datetime import datetime
from typing import Final, Literal
from uuid import UUID

from daily_tasks.domain import (
    Blocker,
    BlockerRef,
    DailyPlan,
    DailyPlanEntry,
    DailyPlanSummary,
    DecisionLogEntry,
    DecisionRef,
    PlanItem,
    StateGraph,
)
from daily_tasks.session.session_state import SessionState
from daily_tasks.storage.cst import DailyPlanDocument, PlanBlockerView, PlanItemView

type _Section = Literal["my-work", "delegated-work", "follow-up-work"]

_SECTIONS: Final[tuple[tuple[str, _Section], ...]] = (
    ("mine", "my-work"),
    ("delegated", "delegated-work"),
    ("follow_up", "follow-up-work"),
)
_MARKS = {"not-started": " ", "in-progress": ">", "completed": "x", "cancelled": "-"}
_SOURCE = "daily-tasks-mcp"


def _link(graph: StateGraph, record_id: UUID, projects_prefix: str) -> str:
    path = next((p for p, rid in graph.index.by_path.items() if rid == record_id), "")
    relative = path.removesuffix(".md")
    return f"{projects_prefix}/{relative}" if projects_prefix else relative


def _item_view(graph: StateGraph, task_id: UUID, projects_prefix: str) -> PlanItemView | None:
    task = graph.records.tasks.get(task_id)
    if task is None:
        return None
    milestone = graph.records.milestones.get(task.milestone_id)
    project = graph.records.projects.get(milestone.project_id) if milestone is not None else None
    return PlanItemView(
        item_id=str(task_id),
        title=task.title,
        path=_link(graph, task_id, projects_prefix),
        project_title=project.title if project is not None else "—",
        milestone_title=milestone.title if milestone is not None else None,
        status_mark=_MARKS.get(task.state, " "),
        due_date=task.target_date,
    )


def _blocker_view(graph: StateGraph, blocker: Blocker, projects_prefix: str) -> PlanBlockerView:
    return PlanBlockerView(
        blocker_id=str(blocker.id),
        title=blocker.title,
        path=_link(graph, blocker.id, projects_prefix),
        impact=blocker.impact,
        owner=blocker.owner,
        resolved_when=blocker.resolved_when,
    )


def _entries(state: SessionState, existing: DailyPlan | None) -> tuple[DailyPlanEntry, ...]:
    graph = state.state_graph
    previous = {entry.item_id: entry for entry in existing.entries} if existing is not None else {}
    now = state.session.updated_at
    entries: list[DailyPlanEntry] = []
    for attribute, section in _SECTIONS:
        items: tuple[PlanItem, ...] = getattr(graph.derived.today.selected, attribute)
        for item in items:
            facts = graph.derived.tasks.get(item.item_id) if item.item_type == "task" else None
            kept = previous.get(item.item_id)
            entries.append(
                DailyPlanEntry(
                    item_type=item.item_type,
                    item_id=item.item_id,
                    section=section,
                    carried_from=facts.carried_from if facts is not None else None,
                    added_at=kept.added_at if kept is not None else now,
                )
            )
    return tuple(entries)


def build_daily_plan_document(
    state: SessionState,
    decisions: Sequence[DecisionLogEntry],
    existing: DailyPlan | None,
    blockers: Mapping[UUID, Blocker],
    projects_prefix: str,
    plan_id: UUID,
    now: datetime,
) -> DailyPlanDocument:
    """Return the plan for the session's local date; `existing` keeps its id, creation time, notes and source.

    Items dropped from an existing plan join `removed_item_ids`; `projects_prefix` is the projects root relative
    to the vault, used for wiki links. Blockers without a record in `blockers` are left out.
    """
    graph = state.state_graph
    session = state.session
    entries = _entries(state, existing)
    selected = {entry.item_id for entry in entries}
    removed = tuple(
        dict.fromkeys(
            (
                *(existing.removed_item_ids if existing is not None else ()),
                *(e.item_id for e in (existing.entries if existing is not None else ()) if e.item_id not in selected),
            )
        )
    )
    blocker_ids = [entry.item_id for entry in entries if entry.item_type == "blocker" and entry.item_id in blockers]
    summary = graph.derived.summary
    plan = DailyPlan(
        id=existing.id if existing is not None else plan_id,
        type="daily-plan",
        local_date=session.local_date,
        timezone=session.timezone,
        path=existing.path if existing is not None else f"{session.local_date:%Y.%m.%d}-daily-plan.md",
        created_at=existing.created_at if existing is not None else now,
        updated_at=now,
        content_hash=existing.content_hash if existing is not None else "",
        focus=session.focus,
        summary=DailyPlanSummary(
            open_projects=summary.open_projects, open_tasks=summary.open_tasks, late_tasks=summary.late_tasks
        ),
        entries=entries,
        removed_item_ids=removed,
        blockers=tuple(
            BlockerRef(blocker_id=b, blocks=tuple(graph.index.blocks.get(b, ()))) for b in dict.fromkeys(blocker_ids)
        ),
        decisions=tuple(DecisionRef(id=d.id, question=d.question, resolution=d.decision) for d in decisions),
        notes=existing.notes if existing is not None else (),
        source=existing.source if existing is not None else _SOURCE,
    )
    views = [_item_view(graph, e.item_id, projects_prefix) for e in entries if e.item_type == "task"]
    return DailyPlanDocument(
        plan=plan,
        owner=graph.context.user.email,
        tags=("plan", "daily"),
        maturity="reviewed",
        record_version=2,
        items=tuple(view for view in views if view is not None),
        blockers=tuple(_blocker_view(graph, blockers[b], projects_prefix) for b in dict.fromkeys(blocker_ids)),
    )
