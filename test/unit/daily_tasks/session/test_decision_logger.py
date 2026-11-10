"""Responsibility: Prove DecisionLogger appends entries through the store and logs one safe outcome.
Public interface:
+-- test_decision_logger_append_entries_stored_and_logged(log_capture)
+-- test_decision_logger_no_entries_writes_nothing(log_capture)
`-- test_decision_logger_store_failure_returns_err_and_logs_error(log_capture)

Decision-log append through an in-memory LocalFileStore fake.
"""

from collections.abc import Sequence
from dataclasses import dataclass, field

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter

from conftest import LogCapture, load_spec
from daily_tasks.domain import DecisionLogEntry, PlanningSession, RecordChange, Suggestions
from daily_tasks.session.decision_logger import DecisionLogger
from daily_tasks.storage.cst import DailyPlanDocument


@dataclass
class _DecisionStore:
    is_failing: bool = False
    log: list[DecisionLogEntry] = field(default_factory=list)

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        return fail("not used", "Unexpected")

    def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]:
        return fail("not used", "Unexpected")

    def save_suggestions(self, suggestions: Suggestions) -> Result[None]:
        return fail("not used", "Unexpected")

    def save_session(self, session: PlanningSession) -> Result[None]:
        return fail("not used", "Unexpected")

    def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]:
        if self.is_failing:
            return fail("decision-log.json is locked", "Unavailable")
        self.log.extend(entries)
        return ok(None)


def _entry() -> DecisionLogEntry:
    return TypeAdapter(DecisionLogEntry).validate_python(load_spec("decision-log-entry.json"))


def test_decision_logger_append_entries_stored_and_logged(log_capture: LogCapture) -> None:
    store = _DecisionStore()

    result = DecisionLogger(store).append([_entry()])

    assert result.ok and result.value == 1
    assert store.log == [_entry()]
    assert [(level, msg) for level, msg, _ in log_capture.records] == [("info", "decisions appended")]
    assert "original_words" not in str(log_capture.records)


def test_decision_logger_store_failure_returns_err_and_logs_error(log_capture: LogCapture) -> None:
    store = _DecisionStore(is_failing=True)

    result = DecisionLogger(store).append([_entry()])

    assert not result.ok
    assert result.category == "Unavailable"
    assert log_capture.records[0][0] == "error" and log_capture.records[0][2]["category"] == "Unavailable"


def test_decision_logger_no_entries_writes_nothing(log_capture: LogCapture) -> None:
    store = _DecisionStore()

    result = DecisionLogger(store).append([])

    assert result.ok and result.value == 0
    assert (store.log, log_capture.records) == ([], [])
