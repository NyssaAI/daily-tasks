"""Responsibility: Choose the rows screen 3 (confirm today's plan) lists, in display order.
Public interface:
`-- confirm_refs(graph)
"""

from daily_tasks.core.planning.row_ref import RowRef
from daily_tasks.core.records.state_graph import StateGraph


def confirm_refs(graph: StateGraph) -> tuple[RowRef, ...]:
    """Return today's task refs before blocker refs, without duplicates."""
    selected = graph.derived.today.selected
    items = (*selected.mine, *selected.delegated, *selected.follow_up)
    tasks = [RowRef(kind="task", id=item.item_id) for item in items if item.record_kind == "task"]
    blockers = [RowRef(kind="blocker", id=item.item_id) for item in items if item.record_kind == "blocker"]
    return tuple(dict.fromkeys((*tasks, *blockers)))
