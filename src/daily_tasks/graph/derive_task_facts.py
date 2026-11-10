"""Responsibility: Compute responsibility, eligibility, lateness, blocking and DoD facts for open tasks.
Public interface:
`-- derive_task_facts(records, relations, plannable_milestones, user_email, local_date)

Facts per open task; completed and cancelled tasks get no facts.
"""

from collections.abc import Set
from datetime import date
from uuid import UUID

from daily_tasks.domain import DodProgress, Task, TaskFacts
from daily_tasks.graph.is_terminal_state import is_terminal_state
from daily_tasks.graph.planned_days import planned_days
from daily_tasks.graph.types import GraphRecords, RecordRelations


def derive_task_facts(
    records: GraphRecords,
    relations: RecordRelations,
    plannable_milestones: Set[UUID],
    user_email: str,
    local_date: date,
) -> dict[UUID, TaskFacts]:
    """Return facts keyed by task id in record order.

    Responsibility is `mine` when the effective assignee (assignee, else owner) is the user, `delegated`
    when the user owns it and someone else is assigned, else `follow-up`. A task is late when its target
    date is before `local_date`, blocked while any blocker on it is open, and closable when its DoD is
    fully checked and it is not blocked. Eligible tasks belong to a plannable milestone.
    """
    planned = planned_days(records.plans, local_date)
    open_blockers = {key for key, blocker in records.blockers.items() if blocker.state == "open"}
    facts: dict[UUID, TaskFacts] = {}
    for task in records.tasks.values():
        if is_terminal_state(task.state):
            continue
        assignee = task.assignee or task.owner
        blocked = any(ref in open_blockers for ref in relations.blocked_by.get(task.id, ()))
        dod = DodProgress(done=sum(item.done for item in task.definition_of_done), total=len(task.definition_of_done))
        eligible = task.milestone_id in plannable_milestones
        planned_for, carried_from = planned.get(task.id, (None, None))
        facts[task.id] = TaskFacts(
            effective_assignee=assignee,
            responsibility=_responsibility(task, assignee, user_email),
            eligible=eligible,
            ineligible_reason=None if eligible else "milestone is not plannable",
            late=task.target_date is not None and task.target_date < local_date,
            blocked=blocked,
            waiting_on=_waiting_on(task, relations, records),
            planned_for=planned_for,
            carried_from=carried_from,
            dod=dod,
            closable=dod.done == dod.total and not blocked,
        )
    return facts


def _responsibility(task: Task, assignee: str, user_email: str) -> str:
    if assignee == user_email:
        return "mine"
    return "delegated" if task.owner == user_email else "follow-up"


def _waiting_on(task: Task, relations: RecordRelations, records: GraphRecords) -> tuple[UUID, ...]:
    return tuple(
        ref for ref in relations.depends_on.get(task.id, ()) if not is_terminal_state(records.tasks[ref].state)
    )
