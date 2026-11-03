# Responsibility: Choose the rows screen 2 (assign days) lists for one project, in display order.
# Public interface:
# `-- assign_days_refs(graph, project_id, include_in_progress)
"""Open tasks of the plannable milestones, then the project's open blockers."""

from uuid import UUID

from daily_tasks.domain import RowRef, StateGraph
from daily_tasks.session.open_task import open_task


def assign_days_refs(graph: StateGraph, project_id: UUID, include_in_progress: bool) -> tuple[RowRef, ...]:
    """The lowest incomplete milestone is plannable; other in-progress ones only when `include_in_progress`."""
    refs: list[RowRef] = []
    for tree in graph.tree:
        if tree.project_id != project_id:
            continue
        for milestone in tree.milestones:
            facts = graph.derived.milestones.get(milestone.milestone_id)
            record = graph.records.milestones.get(milestone.milestone_id)
            is_lowest = facts is not None and facts.lowest_incomplete
            is_extra = include_in_progress and record is not None and record.state == "in-progress"
            if is_lowest or is_extra:
                refs.extend(RowRef(kind="task", id=t) for t in milestone.task_ids if open_task(graph, t))
        for blocker_id in tree.blocker_ids:
            blocker = graph.records.blockers.get(blocker_id)
            if blocker is not None and blocker.state == "open":
                refs.append(RowRef(kind="blocker", id=blocker_id))
    return tuple(refs)
