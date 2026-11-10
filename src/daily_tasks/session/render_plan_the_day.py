"""Responsibility: Render screen 1 (plan the day) as Markdown from the session state.
Public interface:
`-- render_plan_the_day(state)

Current plan rows and pending suggestion rows, numbered exactly as recorded on `s1`.
"""

from uuid import UUID

from pydantic import JsonValue

from daily_tasks.domain import Suggestion
from daily_tasks.session.format_day import format_day
from daily_tasks.session.markdown_table import markdown_table
from daily_tasks.session.screen_rows import screen_rows
from daily_tasks.session.session_state import SessionState
from daily_tasks.session.status_mark import status_mark

_KINDS = {"new-task": "New task", "status": "Status", "dod": "DoD", "blocker": "Blocker"}
_LEGEND = "Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled"


def _values(values: dict[str, JsonValue] | None) -> str:
    if not values:
        return "—"
    return " · ".join(f"{key} {value}" for key, value in values.items())


def _context(state: SessionState, record_id: UUID | None) -> tuple[str, str, str]:
    records = state.state_graph.records
    task = records.tasks.get(record_id) if record_id is not None else None
    if task is None:
        return "—", "—", "—"
    milestone = records.milestones.get(task.milestone_id)
    project = records.projects.get(milestone.project_id) if milestone is not None else None
    return (project.title if project else "—", milestone.title if milestone else "—", task.title)


def _suggestion_row(state: SessionState, number: int, suggestion: Suggestion) -> list[str]:
    target = suggestion.target.record_id if suggestion.target is not None else None
    project, milestone, task = _context(state, target)
    if suggestion.kind == "new-task":
        title = suggestion.proposed.get("title")
        task = str(title) if title is not None else task
    current = dict(suggestion.current) if suggestion.current is not None else None
    return [
        str(number),
        _KINDS[suggestion.kind],
        project,
        milestone,
        f"{task} <!-- ref: {suggestion.id} -->",
        _values(current),
        _values(dict(suggestion.proposed)),
        f'"{suggestion.evidence}"',
        ", ".join(suggestion.source_message_ids),
    ]


def render_plan_the_day(state: SessionState) -> str:
    """Return the plan-the-day screen; suggestion rows appear only once suggestions are numbered."""
    graph = state.state_graph
    records = graph.records
    summary = graph.derived.summary
    suggestions = {s.id: s for s in state.suggestions}
    plan_rows: list[list[str]] = []
    suggestion_rows: list[list[str]] = []
    for number, ref in screen_rows(state.session, "s1"):
        if ref.kind == "suggestion" and ref.id in suggestions:
            suggestion_rows.append(_suggestion_row(state, number, suggestions[ref.id]))
            continue
        task = records.tasks.get(ref.id)
        if ref.kind != "task" or task is None:
            continue
        project, milestone, _ = _context(state, ref.id)
        facts = graph.derived.tasks.get(ref.id)
        carried = "↺ " if facts is not None and facts.carried_from is not None else ""
        plan_rows.append(
            [
                str(number),
                status_mark(task.state),
                project,
                milestone,
                f"{carried}{task.title} <!-- ref: {ref.id} -->",
                task.owner,
                task.assignee or "—",
                format_day(task.target_date),
            ]
        )
    day = graph.context.local_date
    lines = [
        f"**Open projects: {summary.open_projects}**          **Open tasks: {summary.open_tasks}**"
        f"          **Late tasks: {summary.late_tasks}**          **Blockers: {summary.open_blockers}**",
        f"    - {day.strftime('%A')} {format_day(day)} · {graph.context.timezone}",
        "",
        "## Current Plan",
        "",
        markdown_table(["#", "Status", "Project", "Milestone", "Task", "Owner", "Assignee", "Due Date"], plan_rows),
    ]
    if suggestion_rows:
        headers = ["#", "Kind", "Project", "Milestone", "Task", "Current", "Proposed", "Why", "Source"]
        lines += ["", "## Suggested Updates (from messages)", "", markdown_table(headers, suggestion_rows)]
        lines += ["", _LEGEND, "", "Reply `accept`, `reject`, or `edit` with the row numbers."]
    else:
        lines += ["", _LEGEND]
    lines += [
        "",
        '**Ready to review your open projects and tasks?** Reply "yes" to continue, or keep updating the items above.',
    ]
    return "\n".join(lines) + "\n"
