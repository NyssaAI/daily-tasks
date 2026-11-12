"""Responsibility: Locate canonical spec examples, Markdown samples, and capture structured package logs for unit tests.
Public interface:
+-- SAMPLES_ROOT
+-- SPECS_ROOT
+-- load_spec(name)
`-- log_capture()

Shared test helpers for reading `docs/specs/*.json`, `samples/*.md`, and capturing `daily_tasks` stdlib logs.
"""

import json
import logging
from collections.abc import Iterator, Mapping
from pathlib import Path
from typing import Final

import pytest
from pydantic import JsonValue, TypeAdapter

from log_capture import LogCapture as LogCapture

SPECS_ROOT: Final[Path] = Path(__file__).resolve().parents[3] / "docs" / "specs"
SAMPLES_ROOT: Final[Path] = Path(__file__).resolve().parent / "samples"
_JSON: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)


def load_spec(name: str) -> JsonValue:
    """Parse one spec example as plain JSON."""
    return _JSON.validate_python(json.loads((SPECS_ROOT / name).read_text(encoding="utf-8")))


@pytest.fixture(autouse=True)
def _isolate_package_logger() -> Iterator[None]:
    """Restore `daily_tasks` logger state after each test so CLI runs never leak handlers or levels."""
    package_logger = logging.getLogger("daily_tasks")
    previous_level = package_logger.level
    previous_propagate = package_logger.propagate
    previous_handlers = list(package_logger.handlers)
    try:
        yield
    finally:
        package_logger.handlers = previous_handlers
        package_logger.setLevel(previous_level)
        package_logger.propagate = previous_propagate


@pytest.fixture
def log_capture() -> Iterator[LogCapture]:
    """Capture structured `daily_tasks` logs at DEBUG level without propagating to stdout/root."""
    capture = LogCapture()

    class _Handler(logging.Handler):
        def emit(self, record: logging.LogRecord) -> None:
            if record.levelno >= logging.ERROR:
                level = "error"
            elif record.levelno >= logging.WARNING:
                level = "warn"
            elif record.levelno >= logging.INFO:
                level = "info"
            else:
                level = "debug"
            raw_fields = record.__dict__.get("fields")
            fields: dict[str, object] = dict(raw_fields) if isinstance(raw_fields, Mapping) else {}
            raw_op = record.__dict__.get("operation")
            operation = str(raw_op) if isinstance(raw_op, str) else ""
            capture.records.append((level, record.getMessage(), fields))
            capture.operations.append((level, operation, fields))

    package_logger = logging.getLogger("daily_tasks")
    handler = _Handler(level=logging.DEBUG)
    package_logger.setLevel(logging.DEBUG)
    package_logger.propagate = False
    package_logger.addHandler(handler)
    try:
        yield capture
    finally:
        package_logger.removeHandler(handler)
