# Responsibility: Write a validated state change into the state graph records.
# Public interface:
# `-- operation_set_state(graph, record_type, record_id, state)
"""Pure transition on graph records; callers validate with `operation_status_rule` first."""

import dataclasses
from typing import Literal
from uuid import UUID

from daily_tasks.domain import StateGraph


def operation_set_state(
    graph: StateGraph, record_type: Literal["task", "blocker", "milestone", "project"], record_id: UUID, state: str
) -> StateGraph:
    """Return a new graph with the record's state replaced (blocker facts follow the record)."""
    records = graph.records
    derived = graph.derived
    if record_type == "task":
        tasks = {**records.tasks, record_id: dataclasses.replace(records.tasks[record_id], state=state)}
        return dataclasses.replace(graph, records=dataclasses.replace(records, tasks=tasks))
    if record_type == "milestone":
        milestones = {**records.milestones, record_id: dataclasses.replace(records.milestones[record_id], state=state)}
        return dataclasses.replace(graph, records=dataclasses.replace(records, milestones=milestones))
    if record_type == "project":
        projects = {**records.projects, record_id: dataclasses.replace(records.projects[record_id], state=state)}
        return dataclasses.replace(graph, records=dataclasses.replace(records, projects=projects))
    blockers = {**records.blockers, record_id: dataclasses.replace(records.blockers[record_id], state=state)}
    facts = derived.blockers.get(record_id)
    blocker_facts = derived.blockers
    if facts is not None:
        blocker_facts = {**derived.blockers, record_id: dataclasses.replace(facts, state=state)}
    return dataclasses.replace(
        graph,
        records=dataclasses.replace(records, blockers=blockers),
        derived=dataclasses.replace(derived, blockers=blocker_facts),
    )
