"""Responsibility: Represent an immutable StateGraph DTO.
Public interface:
`-- StateGraph
    +-- context
    +-- derived
    +-- diagnostics
    +-- index
    +-- note
    +-- records
    `-- tree

StateGraph DTO.
"""

from pydantic import MISSING, Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.diagnostic import Diagnostic
from daily_tasks.core.records.dto_config import DTO_CONFIG
from daily_tasks.core.records.project_tree import ProjectTree
from daily_tasks.core.records.state_graph_context import StateGraphContext
from daily_tasks.core.records.state_graph_derived import StateGraphDerived
from daily_tasks.core.records.state_graph_index import StateGraphIndex
from daily_tasks.core.records.state_graph_records import StateGraphRecords


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class StateGraph:
    """Point-in-time state graph, rebuilt from the configured record sources."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    context: StateGraphContext
    records: StateGraphRecords
    tree: tuple[ProjectTree, ...]
    index: StateGraphIndex
    derived: StateGraphDerived
    diagnostics: tuple[Diagnostic, ...]
