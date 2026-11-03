# Responsibility: Hold the outcome of one validated operation applied to the state graph.
# Public interface:
# `-- OperationStep
#     +-- change
#     +-- decision
#     `-- graph
"""Single operation outcome: new graph, its decision-log entry and its staged record change."""

from dataclasses import dataclass

from daily_tasks.domain import DecisionLogEntry, RecordChange, StateGraph


@dataclass(frozen=True, slots=True, kw_only=True)
class OperationStep:
    """`change` is None when the operation only affects the daily plan, not a record file."""

    graph: StateGraph
    decision: DecisionLogEntry
    change: RecordChange | None
