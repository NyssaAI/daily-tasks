"""Responsibility: Build a staged record change, locating the record file through the state graph index.
Public interface:
`-- operation_record_change(graph, context, record_type, record_id, before, after)

Pure staged-change construction; the store checks `expected_hash` when it applies the change.
"""

from collections.abc import Mapping
from typing import Literal
from uuid import UUID

from pydantic import JsonValue

from daily_tasks.domain import RecordChange, StateGraph
from daily_tasks.session.operation_context import OperationContext


def operation_record_change(
    graph: StateGraph,
    context: OperationContext,
    record_type: Literal["project", "milestone", "task", "blocker"],
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
        record_type=record_type,
        record_id=record_id,
        path=path,
        expected_hash=graph.index.file_hashes.get(path, ""),
        before=before,
        after=after,
        effects=(),
        status="staged",
        applied_at=None,
    )
