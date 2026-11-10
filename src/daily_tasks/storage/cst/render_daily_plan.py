"""Responsibility: Render a daily plan document as canonical Obsidian Markdown.
Public interface:
+-- SECTION_TITLES
`-- render_daily_plan(document)

Daily plan renderer matching the layout of `docs/specs/8-sample-daily-plan.md`.
"""

from collections.abc import Mapping
from datetime import date, datetime
from typing import Final
from zoneinfo import ZoneInfo

from daily_tasks.domain import DailyPlanEntry
from daily_tasks.storage.cst.parse_frontmatter import format_scalar
from daily_tasks.storage.cst.types import DailyPlanDocument, PlanBlockerView, PlanItemView

SECTION_TITLES: Final[Mapping[str, str]] = {
    "my-work": "My work",
    "delegated-work": "Delegated work",
    "follow-up-work": "Follow-up work",
}
_ITEM_HEADER: Final = "| # | Status | Project | Milestone | Task | Due Date |\n| --- | --- | --- | --- | --- | --- |"
_BLOCKER_HEADER: Final = "| Blocker | Impact | Owner | Resolved When |\n| --- | --- | --- | --- |"
_LEGEND: Final = "Legend: [ ] not started · [>] in progress · [x] completed · [-] cancelled · ↺ carried forward"
_DASH: Final = "—"


def _cell(text: str) -> str:
    return text.replace("|", "\\|")


def _timestamp(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M:%SZ")


def _due(value: date | None) -> str:
    return value.strftime("%Y.%m.%d") if value else _DASH


def _link(path: str, title: str, item_id: str) -> str:
    return f"[[{path}\\|{_cell(title)}]] <!-- ref: {item_id} -->"


def _frontmatter(document: DailyPlanDocument) -> list[str]:
    plan = document.plan
    pairs: list[tuple[str, str]] = [
        ("id", str(plan.id)),
        ("type", plan.type),
        ("record_version", str(document.record_version)),
        ("title", format_scalar(f"Daily plan {plan.local_date.isoformat()}", quoted=True)),
        ("document-maturity", format_scalar(document.maturity, quoted=False)),
        ("timezone", format_scalar(plan.timezone, quoted=True)),
        ("date", format_scalar(plan.local_date.isoformat(), quoted=True)),
        ("owner", format_scalar(document.owner, quoted=True)),
        ("created_at", format_scalar(_timestamp(plan.created_at), quoted=True)),
        ("updated_at", format_scalar(_timestamp(plan.updated_at), quoted=True)),
        ("tags", format_scalar(document.tags, quoted=True)),
    ]
    return ["---", *(f"{key}: {value}" for key, value in pairs), "---"]


def _header(document: DailyPlanDocument) -> list[str]:
    plan = document.plan
    local = plan.updated_at.astimezone(ZoneInfo(plan.timezone))
    summary = plan.summary
    lines = [
        f"# Daily plan — {plan.local_date.isoformat()}",
        "",
        f"Open projects: {summary.open_projects}          Open tasks: {summary.open_tasks}"
        f"          Late tasks: {summary.late_tasks}",
        "",
        f"**Timezone:** {plan.timezone}  ",
        f"**Updated:** {local.strftime('%Y.%m.%d %H:%M')} {local.tzname()}  ",
    ]
    if plan.focus:
        lines.append(f"**Focus:** {plan.focus}")
    return lines


def _item_row(number: int, entry: DailyPlanEntry, view: PlanItemView) -> str:
    carried = "↺ " if entry.carried_from else ""
    cells = (
        str(number),
        f"[{view.status_mark}]",
        _cell(view.project_title),
        _cell(view.milestone_title or _DASH),
        carried + _link(view.path, view.title, view.item_id),
        _due(view.due_date),
    )
    return "| " + " | ".join(cells) + " |"


def _selected(document: DailyPlanDocument, numbers: dict[str, int]) -> list[str]:
    views = {view.item_id: view for view in document.items}
    lines = ["## Selected for today"]
    for section, title in SECTION_TITLES.items():
        entries = [e for e in document.plan.entries if e.section == section and str(e.item_id) in views]
        if not entries:
            continue
        lines += ["", f"### {title}"]
        group: tuple[str, str | None] | None = None
        for entry in entries:
            view = views[str(entry.item_id)]
            if (view.project_title, view.milestone_title) != group:
                group = (view.project_title, view.milestone_title)
                heading = view.project_title + (f" / {view.milestone_title}" if view.milestone_title else "")
                lines += ["", f"#### {heading}", "", _ITEM_HEADER]
            numbers[view.item_id] = len(numbers) + 1
            lines.append(_item_row(numbers[view.item_id], entry, view))
    return [*lines, "", _LEGEND]


def _blocker_row(view: PlanBlockerView, blocks: tuple[str, ...], numbers: Mapping[str, int]) -> str:
    rows = [f"#{numbers[item]}" for item in blocks if item in numbers]
    impact = view.impact + (f" Blocks {', '.join(rows)}." if rows else "")
    cells = (_link(view.path, view.title, view.blocker_id), _cell(impact), _cell(view.owner), _cell(view.resolved_when))
    return "| " + " | ".join(cells) + " |"


def _blockers(document: DailyPlanDocument, numbers: Mapping[str, int]) -> list[str]:
    views = {view.blocker_id: view for view in document.blockers}
    rows = [
        _blocker_row(views[str(ref.blocker_id)], tuple(str(item) for item in ref.blocks), numbers)
        for ref in document.plan.blockers
        if str(ref.blocker_id) in views
    ]
    return ["## Blockers Under Active Resolution", "", *([_BLOCKER_HEADER, *rows] if rows else ["None"])]


def render_daily_plan(document: DailyPlanDocument) -> str:
    """Render the plan with LF endings; entries and blockers without a matching view are left out.

    `document.plan.updated_at` is shown in the plan's IANA timezone, which must exist.
    """
    plan = document.plan
    numbers: dict[str, int] = {}
    decisions = [f"- **[{d.id}]** {d.question} {d.resolution}" for d in plan.decisions]
    notes = [f"- {note}" for note in plan.notes]
    lines = [
        *_frontmatter(document),
        *_header(document),
        "",
        *_selected(document, numbers),
        "",
        *_blockers(document, numbers),
        "",
        "## Decisions",
        "",
        *([*decisions, ""] if decisions else []),
        "## Notes and references",
        *(["", *notes] if notes else []),
    ]
    return "\n".join(lines) + "\n"
