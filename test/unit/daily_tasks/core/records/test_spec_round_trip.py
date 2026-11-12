"""Responsibility: Prove every spec example round-trips through its core payload class without data loss.
Public interface:
+-- SPEC_ADAPTERS
+-- test_spec_example_round_trip_preserves_json(name)
`-- test_spec_types_cover_every_spec_file()

Round-trip parity between `docs/specs/*.json` and the core record, communication, and planning payloads.
"""

import json

import pytest
from pydantic import TypeAdapter

from conftest import SPECS_ROOT, load_spec
from daily_tasks.core.communications import (
    CommunicationMessage,
    FetchCursors,
    MessageGraph,
    MessageLog,
    Suggestions,
)
from daily_tasks.core.planning import (
    DecisionLog,
    DecisionLogEntry,
    Operations,
    PlanningSession,
    PortConfig,
    ToolResults,
)
from daily_tasks.core.records import (
    Blocker,
    DailyPlan,
    Milestone,
    Project,
    RecordChange,
    StateGraph,
    Task,
)

SPEC_ADAPTERS: dict[str, TypeAdapter[object]] = {
    "blocker.json": TypeAdapter(Blocker),
    "daily-plan.json": TypeAdapter(DailyPlan),
    "decision-log-entry.json": TypeAdapter(DecisionLogEntry),
    "decision-log.json": TypeAdapter(DecisionLog),
    "fetch-cursors.json": TypeAdapter(FetchCursors),
    "message-graph.json": TypeAdapter(MessageGraph),
    "message-log.json": TypeAdapter(MessageLog),
    "message.json": TypeAdapter(CommunicationMessage),
    "milestone.json": TypeAdapter(Milestone),
    "operations.json": TypeAdapter(Operations),
    "planning-session.json": TypeAdapter(PlanningSession),
    "port-config.json": TypeAdapter(PortConfig),
    "project.json": TypeAdapter(Project),
    "record-change.json": TypeAdapter(RecordChange),
    "state-graph.json": TypeAdapter(StateGraph),
    "suggestions.json": TypeAdapter(Suggestions),
    "task.json": TypeAdapter(Task),
    "tool-results.json": TypeAdapter(ToolResults),
}


def test_spec_types_cover_every_spec_file() -> None:
    assert sorted(SPEC_ADAPTERS) == sorted(path.name for path in SPECS_ROOT.glob("*.json"))


@pytest.mark.parametrize("name", sorted(SPEC_ADAPTERS))
def test_spec_example_round_trip_preserves_json(name: str) -> None:
    adapter = SPEC_ADAPTERS[name]
    raw = (SPECS_ROOT / name).read_text(encoding="utf-8")

    dto = adapter.validate_json(raw)
    dumped = json.loads(adapter.dump_json(dto))

    assert dumped == load_spec(name)
    assert adapter.validate_python(dumped) == dto
