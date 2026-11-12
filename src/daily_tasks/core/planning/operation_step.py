"""Responsibility: Hold the outcome of one validated operation applied to the state graph.
Public interface:
`-- OperationStep
    +-- change
    +-- decision
    `-- graph

Single operation outcome: new graph, its decision-log entry and its staged record change.
"""

from dataclasses import dataclass

from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.state_graph import StateGraph


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationStep:
    """`change` is None when the operation only affects the daily plan, not a record file."""

    graph: StateGraph
    decision: DecisionLogEntry
    change: RecordChange | None
