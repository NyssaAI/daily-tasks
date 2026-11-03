# Responsibility: Render screen 2 (assign days) for the current project as Markdown.
# Public interface:
# `-- render_assign_days(state)
"""Milestone outline, one task table per plannable milestone and the blocker table, numbered as on `s2:<id>`."""

from datetime import date
from uuid import UUID

from daily_tasks.domain import RowRef, StateGraph
from daily_tasks.session.format_day import format_day
from daily_tasks.session.markdown_table import markdown_table
from daily_tasks.session.screen_rows import screen_rows
from daily_tasks.session.session_state import SessionState
from daily_tasks.session.status_mark import status_mark

_STATES = {"not-started": "not started", "in-progress": "in progress", "completed": "complete"}
_LEGEND = "Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward · ⛔ blocked"
_TASK_HEADERS = ["#", "Task", "Status", "Assignee", "Due Date", "Planned day", "Notes"]


def _planned(day: date | None, today: date) -> str:
    if day is None:
        return "—"
    if day == today:
        return "**Today**"
    return f"**{day.strftime('%a')} {format_day(day)}**"


def _task_row(graph: StateGraph, number: int, task_id: UUID, numbers: dict[UUID, int]) -> list[str]:
    task = graph.records.tasks[task_id]
    facts = graph.derived.tasks.get(task_id)
    carried = "↺ " if facts is not None and facts.carried_from is not None else ""
    notes = [
        f"⛔ #{numbers[b]} {graph.records.blockers[b].title}"
        for b in graph.index.blocked_by.get(task_id, ())
        if b in numbers and b in graph.records.blockers
    ]
    notes += [f"waits on #{numbers[t]}" for t in graph.index.depends_on.get(task_id, ()) if t in numbers]
    planned = facts.planned_for if facts is not None else None
    return [
        str(number),
        f"{carried}{task.title} <!-- ref: {task_id} -->",
        status_mark(task.state),
        task.assignee or "—",
        format_day(task.target_date),
        _planned(planned, graph.context.local_date),
        " · ".join(notes),
    ]


def render_assign_days(state: SessionState) -> str:
    """Return the assign-days screen for `current_project_id`; empty string when no project is shown."""
    graph = state.state_graph
    session = state.session
    project_id = session.assign_days.current_project_id
    tree = next((t for t in graph.tree if t.project_id == project_id), None)
    if project_id is None or tree is None:
        return ""
    rows: list[tuple[int, RowRef]] = list(screen_rows(session, f"s2:{project_id}"))
    numbers = {ref.id: number for number, ref in rows}
    order = session.assign_days.project_order
    day = graph.context.local_date
    lines = [
        f"**Project {order.index(project_id) + 1} of {len(order)}** · {day.strftime('%A')} {format_day(day)}"
        f" · {graph.context.timezone}",
        "",
        f"## {graph.records.projects[project_id].title}",
        "",
    ]
    for milestone in tree.milestones:
        record = graph.records.milestones[milestone.milestone_id]
        lines.append(f"  - M{record.number}: {record.title} ({_STATES.get(record.state, record.state)})")
    for milestone in tree.milestones:
        task_rows = [_task_row(graph, numbers[t], t, numbers) for t in milestone.task_ids if t in numbers]
        if task_rows:
            record = graph.records.milestones[milestone.milestone_id]
            lines += ["", f"## M{record.number}: {record.title}", "", markdown_table(_TASK_HEADERS, task_rows)]
    lines += ["", _LEGEND]
    blocker_rows = []
    for blocker_id in tree.blocker_ids:
        if blocker_id not in numbers:
            continue
        blocker = graph.records.blockers[blocker_id]
        blocked = ", ".join(f"#{numbers[t]}" for t in graph.index.blocks.get(blocker_id, ()) if t in numbers)
        facts = graph.derived.blockers.get(blocker_id)
        planned = _planned(facts.planned_for if facts is not None else None, day)
        title = f"{blocker.title} <!-- ref: {blocker_id} -->"
        blocker_rows.append(
            [str(numbers[blocker_id]), status_mark(blocker.state), title, blocked, blocker.owner, planned]
        )
    if blocker_rows:
        headers = ["#", "Status", "Blocker", "Blocks", "Owner", "Planned day"]
        lines += ["", "## Blockers", "", markdown_table(headers, blocker_rows)]
    is_last = order[-1] == project_id
    prompt = (
        '**Ready to finalize today\'s plan?** Reply "yes" to see the recap, or keep updating.'
        if is_last
        else '**Next project?** Reply "next", "previous" to go back, or "finish" to skip to the plan recap.'
    )
    lines += ["", "A bare list of numbers requires clarification about the intended action.", "", prompt]
    return "\n".join(lines) + "\n"
