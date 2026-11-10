"""Responsibility: Count the headline numbers of the state graph.
Public interface:
`-- derive_summary(records, task_facts, today, rollover, settings)

Open projects, milestones, tasks and blockers, late and blocked tasks, and today's selection size.
"""

from collections.abc import Mapping
from uuid import UUID

from daily_tasks.domain import Rollover, StateGraphSummary, TaskFacts, Today
from daily_tasks.graph.is_terminal_state import is_terminal_state
from daily_tasks.graph.types import GraphRecords, StateGraphSettings


def derive_summary(
    records: GraphRecords,
    task_facts: Mapping[UUID, TaskFacts],
    today: Today,
    rollover: Rollover,
    settings: StateGraphSettings,
) -> StateGraphSummary:
    """Return counts; "open" means not completed, cancelled or resolved. Message and operation counts come
    from `settings` unchanged."""
    selected = today.selected
    return StateGraphSummary(
        open_projects=sum(not is_terminal_state(p.state) for p in records.projects.values()),
        open_milestones=sum(not is_terminal_state(m.state) for m in records.milestones.values()),
        open_tasks=len(task_facts),
        late_tasks=sum(facts.late for facts in task_facts.values()),
        blocked_tasks=sum(facts.blocked for facts in task_facts.values()),
        open_blockers=sum(not is_terminal_state(b.state) for b in records.blockers.values()),
        selected_today=len(selected.mine) + len(selected.delegated) + len(selected.follow_up),
        carried_forward=len(rollover.carried),
        pending_operations=settings.pending_operations,
        unreviewed_messages=settings.unreviewed_messages,
        changed_outside_app=settings.changed_outside_app,
    )
