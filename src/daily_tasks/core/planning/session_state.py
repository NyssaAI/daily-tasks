"""Responsibility: Hold one planning session snapshot with its stage and in-memory inputs.
Public interface:
`-- SessionState
    +-- initial(state_graph, suggestions, session_id, vault_root, suggestions_file, focus, now, message_graph)
    +-- message_graph
    +-- session
    +-- stage
    +-- state_graph
    +-- suggestions
    `-- with_session(session, stage)
"""

import dataclasses
from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from daily_tasks.core.communications.message_graph import MessageGraph
from daily_tasks.core.communications.suggestion import Suggestion
from daily_tasks.core.planning.assign_days import AssignDays
from daily_tasks.core.planning.background_fetch import BackgroundFetch
from daily_tasks.core.planning.planning_session import PlanningSession
from daily_tasks.core.planning.session_stage import SessionStage
from daily_tasks.core.records.state_graph import StateGraph

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
        vault_root: str,
        suggestions_file: str = "suggestions.json",
        focus: str | None = None,
        now: datetime | None = None,
        message_graph: MessageGraph | None = None,
    ) -> "SessionState":
        """Build the INIT state for the graph's local day; no screen is shown and no row is numbered yet."""
        context = state_graph.context
        timestamp = now if now is not None else context.built_at
        session = PlanningSession(
            id=session_id,
            vault_root=vault_root,
            local_date=context.local_date,
            timezone=context.timezone,
            started_at=timestamp,
            updated_at=timestamp,
            confirmed_at=None,
            focus=focus,
            inventory_hash=context.inventory_hash,
            background=BackgroundFetch(status="pending", started_at=timestamp, completed_at=None, sources=()),
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
