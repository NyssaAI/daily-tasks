"""Responsibility: Hold the outcome of adjudicating pending suggestions.
Public interface:
`-- Adjudication
    +-- changes
    +-- decisions
    +-- graph
    `-- suggestions

Suggestion adjudication outcome: pruned pool, updated graph, decisions and staged changes.
"""

from dataclasses import dataclass

from daily_tasks.core.communications.suggestions import Suggestions
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.state_graph import StateGraph


@dataclass(frozen=True, slots=True, kw_only=True)
class Adjudication:
    """`suggestions` keeps only the suggestions the user has not answered."""

    suggestions: Suggestions
    graph: StateGraph
    decisions: tuple[DecisionLogEntry, ...]
    changes: tuple[RecordChange, ...]
