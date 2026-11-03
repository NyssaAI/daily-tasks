# Responsibility: Nest projects, milestones, tasks and blockers into the ordered state graph tree.
# Public interface:
# `-- build_tree(records)
"""Project -> milestone -> task nesting by id, with records whose parent is missing reported."""

from collections.abc import Callable, Iterable, Mapping
from uuid import UUID

from daily_tasks.domain import Blocker, Diagnostic, Milestone, MilestoneTree, Project, ProjectTree, Task
from daily_tasks.graph.types import GraphRecords


def build_tree(records: GraphRecords) -> tuple[tuple[ProjectTree, ...], tuple[Diagnostic, ...]]:
    """Order projects by directory date then title; children by their parent's id list, then by number.

    A child is listed under the parent its own `project_id`/`milestone_id` names, so a stale id list on
    the parent cannot move it. Children whose parent is not among the records get an `ORPHAN_RECORD`
    diagnostic and stay out of the tree.
    """
    projects = sorted(records.projects.values(), key=lambda p: (p.directory_date, p.title, str(p.id)))
    tree = tuple(_project_tree(project, records) for project in projects)
    diagnostics = [
        *_orphans(records.milestones.values(), lambda m: m.project_id, records.projects),
        *_orphans(records.tasks.values(), lambda t: t.milestone_id, records.milestones),
        *_orphans(records.blockers.values(), lambda b: b.project_id, records.projects),
    ]
    return tree, tuple(diagnostics)


def _project_tree(project: Project, records: GraphRecords) -> ProjectTree:
    milestones = _ordered(project.milestone_ids, [m for m in records.milestones.values() if m.project_id == project.id])
    blockers = _ordered(project.blocker_ids, [b for b in records.blockers.values() if b.project_id == project.id])
    return ProjectTree(
        project_id=project.id,
        milestones=tuple(_milestone_tree(milestone, records) for milestone in milestones),
        blocker_ids=tuple(blocker.id for blocker in blockers),
    )


def _milestone_tree(milestone: Milestone, records: GraphRecords) -> MilestoneTree:
    tasks = _ordered(milestone.task_ids, [t for t in records.tasks.values() if t.milestone_id == milestone.id])
    return MilestoneTree(milestone_id=milestone.id, task_ids=tuple(task.id for task in tasks))


def _ordered[R: Milestone | Task | Blocker](listed: Iterable[UUID], children: list[R]) -> list[R]:
    position = {child_id: index for index, child_id in enumerate(listed)}
    return sorted(children, key=lambda c: (position.get(c.id, len(position)), c.number, str(c.id)))


def _orphans[R: Milestone | Task | Blocker](
    children: Iterable[R], parent_of: Callable[[R], UUID], parents: Mapping[UUID, object]
) -> list[Diagnostic]:
    return [
        Diagnostic(
            level="warning",
            code="ORPHAN_RECORD",
            path=child.path,
            detail=f"parent {parent_of(child)} of {child.type} {child.id} not found.",
        )
        for child in children
        if parent_of(child) not in parents
    ]
