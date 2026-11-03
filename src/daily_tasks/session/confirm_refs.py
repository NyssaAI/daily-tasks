# Responsibility: Choose the rows screen 3 (confirm today's plan) lists, in display order.
# Public interface:
# `-- confirm_refs(graph)
"""Tasks selected for today (my work, delegated, follow-up), then blockers selected for today."""

from daily_tasks.domain import RowRef, StateGraph


def confirm_refs(graph: StateGraph) -> tuple[RowRef, ...]:
    """Return today's task refs before blocker refs, without duplicates."""
    selected = graph.derived.today.selected
    items = (*selected.mine, *selected.delegated, *selected.follow_up)
    tasks = [RowRef(kind="task", id=item.item_id) for item in items if item.item_type == "task"]
    blockers = [RowRef(kind="blocker", id=item.item_id) for item in items if item.item_type == "blocker"]
    return tuple(dict.fromkeys((*tasks, *blockers)))
