# Responsibility: Prove ConfirmPlan commits record changes then the daily plan only after explicit confirmation.
# Public interface:
# (none)
"""Confirm-plan persistence order and refusal through an in-memory LocalFileStore fake."""

import dataclasses
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from itertools import count
from uuid import UUID

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import (
    DailyPlan,
    DecisionLogEntry,
    Operations,
    PlanningSession,
    RecordChange,
    StateGraph,
    Suggestions,
)
from daily_tasks.session.apply_operations import apply_operations
from daily_tasks.session.confirm_plan import ConfirmPlan
from daily_tasks.storage.cst import DailyPlanDocument

NOW = datetime(2026, 11, 3, 14, 24, tzinfo=UTC)
GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
GMAIL_PATH = "2026.10.20-daily-tasks-mcp-server/m2-planning-session-spike/t1-wire-gmail-connector.md"


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


@dataclass
class _MemoryStore:
    file_hashes: dict[str, str] = field(default_factory=lambda: {GMAIL_PATH: "sha256:31be09aa77"})
    writes: list[str] = field(default_factory=list)
    applied: list[RecordChange] = field(default_factory=list)

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        if any(self.file_hashes.get(c.path, "") != c.expected_hash for c in changes):
            return fail("record changed outside the app", "Conflict")
        done = tuple(dataclasses.replace(c, status="applied", applied_at=NOW) for c in changes)
        self.applied.extend(done)
        self.writes.append("apply")
        return ok(done)

    def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]:
        self.writes.append("plan")
        return ok(f"daily-plans/{document.plan.local_date:%Y.%m.%d}-daily-plan.md")

    def save_suggestions(self, suggestions: Suggestions) -> Result[None]:
        return ok(None)

    def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]:
        return ok(None)

    def save_session(self, session: PlanningSession) -> Result[None]:
        return ok(None)


def _document() -> DailyPlanDocument:
    plan = TypeAdapter(DailyPlan).validate_python(load_spec("daily-plan.json"))
    return DailyPlanDocument(
        plan=plan, owner="jordan@example.com", tags=(), maturity="reviewed", record_version=2, items=(), blockers=()
    )


def _staged_changes() -> tuple[RecordChange, ...]:
    graph = TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))
    request = TypeAdapter(Operations).validate_python(
        {
            "session_id": "019a4b2c-9000-7000-8000-0000000000a1",
            "screen_id": "s2",
            "original_words": "3 owner alex@example.com",
            "actor": {"kind": "person", "id": "jordan@example.com"},
            "operations": [
                {
                    "kind": "reassign",
                    "row": 3,
                    "item_type": "task",
                    "item_id": str(GMAIL_TASK),
                    "owner": "alex@example.com",
                }
            ],
        }
    )
    numbers = count(1)
    result = apply_operations(graph, request, lambda: UUID(f"019a4b2c-9000-7000-8000-{next(numbers):012x}"), NOW)
    assert result.ok
    return result.value.changes


def test_confirm_plan_confirmed_applies_changes_then_writes_plan() -> None:
    store, logger = _MemoryStore(), _RecordingLogger()
    changes = _staged_changes()

    result = ConfirmPlan(store, logger).confirm(changes, _document(), confirmed_by_user=True)

    assert result.ok and result.value == "daily-plans/2026.11.03-daily-plan.md"
    assert store.writes == ["apply", "plan"]
    assert [c.status for c in store.applied] == ["applied"]
    assert [(level, msg) for level, msg, _ in logger.records] == [("info", "plan confirmed")]
    assert logger.records[0][2]["changes"] == 1


def test_confirm_plan_not_confirmed_writes_nothing() -> None:
    store, logger = _MemoryStore(), _RecordingLogger()

    result = ConfirmPlan(store, logger).confirm(_staged_changes(), _document(), confirmed_by_user=False)

    assert not result.ok
    assert "not_confirmed" in result.message and result.category == "Forbidden"
    assert store.writes == []
    assert logger.records[0][0] == "warn"


def test_confirm_plan_conflict_stops_plan_write() -> None:
    store, logger = _MemoryStore(file_hashes={GMAIL_PATH: "sha256:edited-outside"}), _RecordingLogger()

    result = ConfirmPlan(store, logger).confirm(_staged_changes(), _document(), confirmed_by_user=True)

    assert not result.ok and result.category == "Conflict"
    assert store.writes == []
    assert logger.records[0][0] == "error" and logger.records[0][2]["category"] == "Conflict"
