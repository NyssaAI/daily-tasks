"""Responsibility: Verify central stdlib-to-Nyssa logging setup, dynamic level changes, and sink failure isolation.
Public interface:
+-- test_logging_setup_contains_sink_failures_and_counts_lost_records()
`-- test_logging_setup_writes_structured_json_without_touching_stdout(tmp_path, capsys)

Unit tests for `daily_tasks.logging_setup`.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import NoReturn

import pytest

from daily_tasks.logging_setup import LOG_LEVEL_ENV_VAR, logging_setup


class _FailingProvider:
    def create_logger(self, category_name: str) -> NoReturn:
        raise OSError(f"sink unavailable for {category_name}")


def test_logging_setup_writes_structured_json_without_touching_stdout(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    log_file = tmp_path / "daily-tasks.jsonl"
    package_logger = logging_setup({LOG_LEVEL_ENV_VAR: "Information"}, str(log_file))
    child = logging.getLogger("daily_tasks.test_sink")

    child.debug("ignored debug", extra={"operation": "test.debug", "fields": {"step": 1}})
    child.info("session ready", extra={"operation": "test.info", "fields": {"count": 2}})
    package_logger.setLevel(logging.DEBUG)
    child.debug("enabled dynamically", extra={"operation": "test.dynamic", "fields": {"step": 3}})

    captured = capsys.readouterr()
    assert captured.out == ""
    assert "session ready" in captured.err
    lines = [json.loads(line) for line in log_file.read_text(encoding="utf-8").splitlines()]
    assert [entry["Message"] for entry in lines] == ["session ready", "enabled dynamically"]
    assert [entry["Operation"] for entry in lines] == ["test.info", "test.dynamic"]
    assert lines[0]["AdditionalFields"] == {"count": 2}


def test_logging_setup_contains_sink_failures_and_counts_lost_records() -> None:
    package_logger = logging_setup(
        {LOG_LEVEL_ENV_VAR: "Debug"},
        provider_factory=lambda _file_path, _level: _FailingProvider(),
    )
    child = logging.getLogger("daily_tasks.broken_sink")

    child.error("storage failed", extra={"operation": "test.fail", "error": RuntimeError("boom")})

    bridge_handlers = [h for h in package_logger.handlers if "lost_records" in vars(h)]
    assert len(bridge_handlers) == 1
    assert vars(bridge_handlers[0])["lost_records"] == 1
