"""Responsibility: Project the source records onto the flat records layer of the state graph.
Public interface:
`-- build_record_nodes(records)

Record fields the graph keeps in memory, keyed by id; daily plans keyed by local date.
"""

from daily_tasks.domain import BlockerNode, DailyPlan, MilestoneNode, PlanNode, ProjectNode, StateGraphRecords, TaskNode
from daily_tasks.graph.types import GraphRecords


def build_record_nodes(records: GraphRecords) -> StateGraphRecords:
    """Return the records layer; a plan's `completed_ids` are its listed tasks that are now completed."""
    return StateGraphRecords(
        projects={
            key: ProjectNode(title=p.title, state=p.state, owner=p.owner, directory_date=p.directory_date)
            for key, p in records.projects.items()
        },
        milestones={
            key: MilestoneNode(project_id=m.project_id, number=m.number, title=m.title, state=m.state)
            for key, m in records.milestones.items()
        },
        tasks={
            key: TaskNode(
                milestone_id=t.milestone_id,
                title=t.title,
                state=t.state,
                owner=t.owner,
                assignee=t.assignee,
                target_date=t.target_date,
            )
            for key, t in records.tasks.items()
        },
        blockers={
            key: BlockerNode(project_id=b.project_id, title=b.title, state=b.state, owner=b.owner)
            for key, b in records.blockers.items()
        },
        plans={day: _plan_node(plan, records) for day, plan in records.plans.items()},
    )


def _plan_node(plan: DailyPlan, records: GraphRecords) -> PlanNode:
    task_ids = tuple(entry.item_id for entry in plan.entries if entry.item_type == "task")
    completed = tuple(
        task_id for task_id in task_ids if task_id in records.tasks and records.tasks[task_id].state == "completed"
    )
    return PlanNode(path=plan.path, task_ids=task_ids, completed_ids=completed)
