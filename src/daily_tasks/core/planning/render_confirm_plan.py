"""Responsibility: Render screen 3 (confirm today's plan) as Markdown.
Public interface:
`-- render_confirm_plan(state)

Today's tasks grouped into my work and delegated work, then today's blockers, numbered as on `s3`.
"""

from uuid import UUID

from daily_tasks.core.planning.format_day import format_day
from daily_tasks.core.planning.markdown_table import markdown_table
from daily_tasks.core.planning.screen_rows import screen_rows
from daily_tasks.core.planning.session_state import SessionState
from daily_tasks.core.planning.status_mark import status_mark
from daily_tasks.core.records.state_graph import StateGraph

_TASK_HEADERS = ["#", "Status", "Project", "Milestone", "Task", "Assignee", "Due Date", "Notes"]


def _task_row(graph: StateGraph, number: int, task_id: UUID, numbers: dict[UUID, int]) -> list[str]:
    records = graph.records
    task = records.tasks[task_id]
    milestone = records.milestones.get(task.milestone_id)
    project = records.projects.get(milestone.project_id) if milestone is not None else None
    facts = graph.derived.tasks.get(task_id)
    carried = "↺ " if facts is not None and facts.carried_from is not None else ""
    notes = [
        f"⛔ {records.blockers[b].title}" for b in graph.index.blocked_by.get(task_id, ()) if b in records.blockers
    ]
    notes += [f"waits on #{numbers[t]}" for t in graph.index.depends_on.get(task_id, ()) if t in numbers]
    return [
        str(number),
        status_mark(task.state),
        project.title if project else "—",
        milestone.title if milestone else "—",
        f"{carried}{task.title} <!-- ref: {task_id} -->",
        task.assignee or "—",
        format_day(task.target_date),
        " · ".join(notes),
    ]


def render_confirm_plan(state: SessionState) -> str:
    """Return the recap; pending suggestions are reported as unanswered and stay pending."""
    graph = state.state_graph
    rows = screen_rows(state.session, "s3")
    numbers = {ref.id: number for number, ref in rows}
    user_identifiers = {
        graph.context.user.email.casefold(),
        *([graph.context.user.name.casefold()] if graph.context.user.name else []),
    }
    mine: list[list[str]] = []
    delegated: list[list[str]] = []
    blockers: list[list[str]] = []
    for number, ref in rows:
        if ref.kind == "task" and ref.id in graph.records.tasks:
            facts = graph.derived.tasks.get(ref.id)
            task = graph.records.tasks[ref.id]
            assignee = facts.effective_assignee if facts is not None else (task.assignee or task.owner)
            target = mine if (assignee and assignee.casefold() in user_identifiers) else delegated
            target.append(_task_row(graph, number, ref.id, numbers))
        elif ref.kind == "blocker" and ref.id in graph.records.blockers:
            blocker = graph.records.blockers[ref.id]
            blocked = ", ".join(
                f"#{numbers[t]} {graph.records.tasks[t].title}"
                for t in graph.index.blocks.get(ref.id, ())
                if t in numbers and t in graph.records.tasks
            )
            title = f"{blocker.title} <!-- ref: {ref.id} -->"
            blockers.append([str(number), status_mark(blocker.state), title, blocked, blocker.owner])
    late = sum(1 for _, ref in rows if (f := graph.derived.tasks.get(ref.id)) is not None and f.late)
    day = graph.context.local_date
    lines = [
        f"**Daily plan — {day.strftime('%A')} {format_day(day)}** · {graph.context.timezone}",
        "",
        f"**Planned today: {len(mine) + len(delegated)}**          **Mine: {len(mine)}**"
        f"          **Delegated: {len(delegated)}**          **Late: {late}**",
    ]
    if state.suggestions:
        count = len(state.suggestions)
        noun = "suggestion" if count == 1 else "suggestions"
        lines += ["", f"⚠ **{count} {noun} still unanswered.** They stay pending if you confirm now."]
    lines += ["", "## My work", "", markdown_table(_TASK_HEADERS, mine)]
    lines += ["", "## Delegated work", "", markdown_table(_TASK_HEADERS, delegated)]
    if blockers:
        headers = ["#", "Status", "Blocker", "Blocks", "Owner"]
        lines += ["", "## Blockers", "", markdown_table(headers, blockers)]
        lines += ["", "Legend: [ ] open · [x] completed (resolved)"]
    lines += ["", "**Confirm today's plan?**"]
    return "\n".join(lines) + "\n"
