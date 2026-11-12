"""Responsibility: Show the assign-days screen for one project with session numbering and milestone labels.
Public interface:
`-- show_project(state, project_id, now)

Enter `s2:<project_id>`: rows continue the session numbering, labels M1, M2… map to milestone ids.
"""

import dataclasses
from datetime import datetime
from uuid import UUID

from daily_tasks.core.planning.assign_days_refs import assign_days_refs
from daily_tasks.core.planning.number_screen import number_screen
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.planning.session_state import SessionState


def show_project(state: SessionState, project_id: UUID, now: datetime) -> SessionState:
    """Return the state at SCREEN_2 showing `project_id`; the caller has already checked the stage."""
    graph = state.state_graph
    session = state.session
    refs = assign_days_refs(graph, project_id, session.assign_days.include_in_progress_milestones)
    labels: dict[str, UUID] = {}
    for tree in graph.tree:
        if tree.project_id == project_id:
            for milestone in tree.milestones:
                record = graph.records.milestones.get(milestone.milestone_id)
                if record is not None:
                    labels[f"M{record.number}"] = milestone.milestone_id
    session = dataclasses.replace(
        session,
        assign_days=dataclasses.replace(session.assign_days, current_project_id=project_id),
        labels={**session.labels, project_id: labels},
    )
    session = number_screen(session, f"s2:{project_id}", "assign-days", refs, now)
    return state.with_session(session, SessionStage.SCREEN_2)
