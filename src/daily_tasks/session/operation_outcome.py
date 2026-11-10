"""Responsibility: Hold the outcome of a validated batch of user operations.
Public interface:
`-- OperationOutcome
    +-- changes
    +-- decisions
    `-- graph

Batch outcome: updated graph, decision-log entries to append and record changes to stage.
"""

from dataclasses import dataclass

from daily_tasks.domain import DecisionLogEntry, RecordChange, StateGraph


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationOutcome:
    """Nothing here is persisted yet; `ConfirmPlan` applies `changes` after explicit confirmation."""

    graph: StateGraph
    decisions: tuple[DecisionLogEntry, ...]
    changes: tuple[RecordChange, ...]
