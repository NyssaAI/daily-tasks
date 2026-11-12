"""Responsibility: Build a staged record change, locating the record file through the state graph index.
Public interface:
`-- operation_record_change(graph, context, record_kind, record_id, before, after)
"""

from collections.abc import Mapping
from uuid import UUID

from pydantic import JsonValue

from daily_tasks.core.planning.operation_context import OperationContext
from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.state_graph import StateGraph


def operation_record_change(
    graph: StateGraph,
    context: OperationContext,
    record_kind: RecordKind,
    record_id: UUID,
    before: Mapping[str, JsonValue] | None,
    after: Mapping[str, JsonValue],
) -> RecordChange:
    """Return a `staged` change; path and hash are empty when the graph has no file for the record."""
    path = next((p for p, rid in graph.index.by_path.items() if rid == record_id), "")
    return RecordChange(
        id=context.new_id(),
        operation_id=context.operation_id,
        origin=context.change_origin,
        record_kind=record_kind,
        record_id=record_id,
        path=path,
        expected_hash=graph.index.file_hashes.get(path, ""),
        before=before,
        after=after,
        effects=(),
        status="staged",
        applied_at=None,
    )
