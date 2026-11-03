# Responsibility: Hold one planning session snapshot with its stage and in-memory inputs.
# Public interface:
# `-- SessionState
#     +-- initial(state_graph, suggestions, session_id, workspace_root, suggestions_file, focus, now, message_graph)
#     +-- message_graph
#     +-- session
#     +-- stage
#     +-- state_graph
#     +-- suggestions
#     `-- with_session(session, stage)
"""Planning session state: the persisted `PlanningSession` plus RAM-only graphs and pending suggestions."""

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from daily_tasks.domain import AssignDays, BackgroundFetch, MessageGraph, PlanningSession, StateGraph, Suggestion
from daily_tasks.session.session_stage import SessionStage

_PROJECT_ORDER_RULE = "project directory date prefix, ascending"


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionState:
    """Immutable session snapshot; transitions build new instances and never accept suggestions."""

    session: PlanningSession
    stage: SessionStage
    suggestions: tuple[Suggestion, ...]
    state_graph: StateGraph
    message_graph: MessageGraph | None = None

    @classmethod
    def initial(
        cls,
        state_graph: StateGraph,
        suggestions: tuple[Suggestion, ...],
        session_id: UUID,
        workspace_root: str,
        suggestions_file: str,
        focus: str | None,
        now: datetime,
        message_graph: MessageGraph | None = None,
    ) -> "SessionState":
        """Build the INIT state for the graph's local day; no screen is shown and no row is numbered yet."""
        context = state_graph.context
        session = PlanningSession(
            id=session_id,
            workspace_root=workspace_root,
            local_date=context.local_date,
            timezone=context.timezone,
            started_at=now,
            updated_at=now,
            confirmed_at=None,
            focus=focus,
            inventory_hash=context.inventory_hash,
            background=BackgroundFetch(status="pending", started_at=now, completed_at=None, sources=()),
            suggestions_file=suggestions_file,
            current_screen="",
            assign_days=AssignDays(
                project_order=state_graph.index.project_order,
                project_order_rule=_PROJECT_ORDER_RULE,
                current_project_id=None,
                include_in_progress_milestones=True,
            ),
            next_row=1,
            rows={},
            labels={},
            screens={},
        )
        return cls(
            session=session,
            stage=SessionStage.INIT,
            suggestions=suggestions,
            state_graph=state_graph,
            message_graph=message_graph,
        )

    def with_session(self, session: PlanningSession, stage: SessionStage) -> "SessionState":
        """Return a copy carrying `session` at `stage`."""
        return dataclasses.replace(self, session=session, stage=stage)
