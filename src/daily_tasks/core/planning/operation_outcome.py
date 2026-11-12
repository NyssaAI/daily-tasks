"""Responsibility: Hold the outcome of a validated batch of user operations.
Public interface:
`-- OperationOutcome
    +-- changes
    +-- decisions
    `-- graph

Batch outcome: updated graph, decision-log entries to append and record changes to stage.
"""

from dataclasses import dataclass

from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.state_graph import StateGraph


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationOutcome:
    """Nothing here is persisted yet; `ConfirmPlan` applies `changes` after explicit confirmation."""

    graph: StateGraph
    decisions: tuple[DecisionLogEntry, ...]
    changes: tuple[RecordChange, ...]
