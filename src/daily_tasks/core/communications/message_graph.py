"""Responsibility: Represent an immutable MessageGraph DTO.
Public interface:
`-- MessageGraph
    +-- context
    +-- derived
    +-- diagnostics
    +-- index
    +-- note
    +-- records
    `-- tree

MessageGraph DTO.
"""

from collections.abc import Mapping

from pydantic import MISSING, Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.message_graph_context import MessageGraphContext
from daily_tasks.core.communications.message_graph_derived import MessageGraphDerived
from daily_tasks.core.communications.message_graph_index import MessageGraphIndex
from daily_tasks.core.communications.message_graph_record import MessageGraphRecord
from daily_tasks.core.communications.message_source_tree import MessageSourceTree
from daily_tasks.core.records.diagnostic import Diagnostic
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class MessageGraph:
    """Point-in-time message graph, rebuilt from the message log and message files."""

    note: str | MISSING = Field(default=MISSING, alias="_note")
    context: MessageGraphContext
    records: Mapping[str, MessageGraphRecord]
    tree: tuple[MessageSourceTree, ...]
    index: MessageGraphIndex
    derived: MessageGraphDerived
    diagnostics: tuple[Diagnostic, ...]
