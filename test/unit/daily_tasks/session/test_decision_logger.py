# Responsibility: Prove DecisionLogger appends entries through the store and logs one safe outcome.
# Public interface:
# (none)
"""Decision-log append through an in-memory LocalFileStore fake."""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import DecisionLogEntry, PlanningSession, RecordChange, Suggestions
from daily_tasks.session.decision_logger import DecisionLogger
from daily_tasks.storage.cst import DailyPlanDocument


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


def test_decision_logger_append_entries_stored_and_logged() -> None:
    store, logger = _DecisionStore(), _RecordingLogger()

    result = DecisionLogger(store, logger).append([_entry()])

    assert result.ok and result.value == 1
    assert store.log == [_entry()]
    assert [(level, msg) for level, msg, _ in logger.records] == [("info", "decisions appended")]
    assert "original_words" not in str(logger.records)


def test_decision_logger_store_failure_returns_err_and_logs_error() -> None:
    store, logger = _DecisionStore(is_failing=True), _RecordingLogger()

    result = DecisionLogger(store, logger).append([_entry()])

    assert not result.ok
    assert result.category == "Unavailable"
    assert logger.records[0][0] == "error" and logger.records[0][2]["category"] == "Unavailable"


def test_decision_logger_no_entries_writes_nothing() -> None:
    store, logger = _DecisionStore(), _RecordingLogger()

    result = DecisionLogger(store, logger).append([])

    assert result.ok and result.value == 0
    assert (store.log, logger.records) == ([], [])
