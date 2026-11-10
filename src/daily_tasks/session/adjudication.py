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

from daily_tasks.domain import DecisionLogEntry, RecordChange, StateGraph, Suggestions


@dataclass(frozen=True, slots=True, kw_only=True)
class Adjudication:
    """`suggestions` keeps only the suggestions the user has not answered."""

    suggestions: Suggestions
    graph: StateGraph
    decisions: tuple[DecisionLogEntry, ...]
    changes: tuple[RecordChange, ...]
