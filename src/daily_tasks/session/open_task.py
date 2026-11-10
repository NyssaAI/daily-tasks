"""Responsibility: Tell whether a state graph task is still open for planning.
Public interface:
`-- open_task(graph, task_id)

A task is open when it exists and is neither completed nor cancelled.
"""

from uuid import UUID

from daily_tasks.domain import StateGraph

_CLOSED = frozenset({"completed", "cancelled"})


def open_task(graph: StateGraph, task_id: UUID) -> bool:
    """Return True when `task_id` is a known task that is not completed or cancelled."""
    task = graph.records.tasks.get(task_id)
    return task is not None and task.state not in _CLOSED
