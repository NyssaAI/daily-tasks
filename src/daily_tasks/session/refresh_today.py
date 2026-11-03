# Responsibility: Recompute today's selection after operations changed planned days.
# Public interface:
# `-- refresh_today(graph)
"""Pure projection of `planned_for` facts back into `derived.today` and its summary count."""

import dataclasses
from uuid import UUID

from daily_tasks.domain import PlanItem, StateGraph, TodaySelection

_SECTION_BY_RESPONSIBILITY = {"mine": "mine", "delegated": "delegated", "follow-up": "follow_up"}


def _planned_today(graph: StateGraph, item: PlanItem) -> bool:
    day = graph.context.local_date
    if item.item_type == "task":
        facts = graph.derived.tasks.get(item.item_id)
        return facts is None or facts.planned_for == day
    blocker = graph.derived.blockers.get(item.item_id)
    return blocker is None or blocker.planned_for == day


def _blocker_section(graph: StateGraph, blocker_id: UUID) -> str:
    facts = graph.derived.blockers[blocker_id]
    return "mine" if facts.owner == graph.context.user.email else "follow_up"


def refresh_today(graph: StateGraph) -> StateGraph:
    """Return `graph` whose today selection matches the items planned for its local date.

    Items already selected keep their section and order (closed items without facts stay); newly planned tasks
    join the section of their responsibility, newly planned blockers join my work when the user owns them.
    """
    day = graph.context.local_date
    current = graph.derived.today.selected
    sections: dict[str, list[PlanItem]] = {
        "mine": [item for item in current.mine if _planned_today(graph, item)],
        "delegated": [item for item in current.delegated if _planned_today(graph, item)],
        "follow_up": [item for item in current.follow_up if _planned_today(graph, item)],
    }
    known = {item.item_id for items in sections.values() for item in items}
    for task_id, facts in graph.derived.tasks.items():
        if facts.planned_for == day and task_id not in known:
            section = _SECTION_BY_RESPONSIBILITY.get(facts.responsibility, "mine")
            sections[section].append(PlanItem(item_type="task", item_id=task_id))
    for blocker_id, blocker in graph.derived.blockers.items():
        if blocker.planned_for == day and blocker_id not in known:
            sections[_blocker_section(graph, blocker_id)].append(PlanItem(item_type="blocker", item_id=blocker_id))
    selected = TodaySelection(
        mine=tuple(sections["mine"]), delegated=tuple(sections["delegated"]), follow_up=tuple(sections["follow_up"])
    )
    available = tuple(
        task_id for task_id, facts in graph.derived.tasks.items() if facts.eligible and facts.planned_for is None
    )
    today = dataclasses.replace(graph.derived.today, selected=selected, available=available)
    count = len(selected.mine) + len(selected.delegated) + len(selected.follow_up)
    summary = dataclasses.replace(graph.derived.summary, selected_today=count)
    return dataclasses.replace(graph, derived=dataclasses.replace(graph.derived, today=today, summary=summary))
