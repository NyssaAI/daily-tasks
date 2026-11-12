"""Responsibility: Prove DecisionLogger appends entries to DecisionLogStoreJson and logs one safe outcome.
Public interface:
+-- test_decision_logger_append_entries_stored_and_logged(tmp_path, log_capture)
+-- test_decision_logger_no_entries_writes_nothing(tmp_path, log_capture)
`-- test_decision_logger_store_failure_returns_err_and_logs_error(tmp_path, log_capture)

Decision-log append through `DecisionLogStoreJson` in `runtime_root`.
"""

import json
from pathlib import Path

from pydantic import TypeAdapter

from conftest import LogCapture, load_spec
from daily_tasks.core.planning import DecisionLogEntry
from daily_tasks.planning import DecisionLogger, DecisionLogStoreJson


def _entry() -> DecisionLogEntry:
    return TypeAdapter(DecisionLogEntry).validate_python(load_spec("decision-log-entry.json"))


def test_decision_logger_append_entries_stored_and_logged(tmp_path: Path, log_capture: LogCapture) -> None:
    store = DecisionLogStoreJson(tmp_path, "/vault")

    result = DecisionLogger(store).append([_entry()])

    assert result.ok and result.value == 1
    persisted = json.loads((tmp_path / "decision-log.json").read_text(encoding="utf-8"))
    assert persisted["vault_root"] == "/vault"
    assert len(persisted["entries"]) == 1
    assert [(level, msg) for level, msg, _ in log_capture.records] == [
        ("info", "decision log updated"),
        ("info", "decisions appended"),
    ]
    assert "original_words" not in str(log_capture.records)


def test_decision_logger_store_failure_returns_err_and_logs_error(tmp_path: Path, log_capture: LogCapture) -> None:
    # Make decision-log.json unreadable/corrupt JSON to trigger store failure
    (tmp_path / "decision-log.json").write_text("{corrupt", encoding="utf-8")
    store = DecisionLogStoreJson(tmp_path, "/vault")

    result = DecisionLogger(store).append([_entry()])

    assert not result.ok
    assert log_capture.records[0][0] == "error"


def test_decision_logger_no_entries_writes_nothing(tmp_path: Path, log_capture: LogCapture) -> None:
    store = DecisionLogStoreJson(tmp_path, "/vault")

    result = DecisionLogger(store).append([])

    assert result.ok and result.value == 0
    assert not (tmp_path / "decision-log.json").exists()
    assert log_capture.records == []
