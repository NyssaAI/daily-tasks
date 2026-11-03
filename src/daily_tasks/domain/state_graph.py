# Responsibility: Represent an immutable StateGraph DTO.
# Public interface:
# `-- StateGraph
#     +-- context
#     +-- derived
#     +-- diagnostics
#     +-- index
#     +-- note
#     +-- records
#     `-- tree
"""StateGraph DTO."""

from pydantic import Field, MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.diagnostic import Diagnostic
from daily_tasks.domain.project_tree import ProjectTree
from daily_tasks.domain.state_graph_context import StateGraphContext
from daily_tasks.domain.state_graph_derived import StateGraphDerived
from daily_tasks.domain.state_graph_index import StateGraphIndex
from daily_tasks.domain.state_graph_records import StateGraphRecords


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

