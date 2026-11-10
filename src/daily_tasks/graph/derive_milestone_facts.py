"""Responsibility: Compute plannability and task progress facts for every milestone.
Public interface:
`-- derive_milestone_facts(records, relations, tree)

Lowest incomplete milestone per project, open/total task counts and closability.
"""

from uuid import UUID

from pydantic import MISSING

from daily_tasks.domain import Milestone, MilestoneFacts, ProjectTree
from daily_tasks.graph.is_terminal_state import is_terminal_state
from daily_tasks.graph.types import GraphRecords, RecordRelations


def derive_milestone_facts(
    records: GraphRecords, relations: RecordRelations, tree: tuple[ProjectTree, ...]
) -> dict[UUID, MilestoneFacts]:
    """Return facts keyed by milestone id in tree order.

    The first incomplete milestone of each project is the lowest incomplete one; later in-progress
    milestones are marked `in_progress_plannable`. Cancelled tasks are not counted. A milestone is
    closable while incomplete, with no open tasks, a fully checked DoD and no open blocker.
    """
    facts: dict[UUID, MilestoneFacts] = {}
    for project_node in tree:
        lowest_found = False
        for milestone_node in project_node.milestones:
            milestone = records.milestones[milestone_node.milestone_id]
            incomplete = not is_terminal_state(milestone.state)
            lowest = incomplete and not lowest_found
            lowest_found = lowest_found or lowest
            states = [records.tasks[task_id].state for task_id in milestone_node.task_ids]
            counted = [state for state in states if state != "cancelled"]
            tasks_open = sum(not is_terminal_state(state) for state in counted)
            facts[milestone.id] = MilestoneFacts(
                lowest_incomplete=lowest,
                in_progress_plannable=True if not lowest and milestone.state == "in-progress" else MISSING,
                tasks_open=tasks_open,
                tasks_total=len(counted),
                closable=incomplete and tasks_open == 0 and _done_and_unblocked(milestone, relations, records),
            )
    return facts


def _done_and_unblocked(milestone: Milestone, relations: RecordRelations, records: GraphRecords) -> bool:
    dod_done = all(item.done for item in milestone.definition_of_done)
    blocked = any(records.blockers[ref].state == "open" for ref in relations.blocked_by.get(milestone.id, ()))
    return dod_done and not blocked
