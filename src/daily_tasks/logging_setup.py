"""Responsibility: Configure standard-library operational logging routed through Nyssa stderr and JSON file sinks.
Public interface:
+-- LOG_LEVEL_ENV_VAR
`-- logging_setup(environ, file_path, provider_factory)

Configure `logging.getLogger('daily_tasks')` with stderr + optional JSON file output and sink isolation.
"""

from __future__ import annotations

import logging
from collections.abc import Callable, Mapping
from typing import Final

from nyssa_ai_logging import (  # type: ignore[import-untyped]  # package ships no py.typed
    LoggerProvider,
    create_nyssa_logging,
    parse_log_level,
)

LOG_LEVEL_ENV_VAR: Final = "DAILY_TASKS_LOG_LEVEL"
_PACKAGE_LOGGER_NAME: Final = "daily_tasks"
_HANDLER_MARKER: Final = "_daily_tasks_nyssa_bridge"

_PYTHON_LEVELS: Final[Mapping[str, int]] = {
    "Trace": logging.DEBUG,
    "Debug": logging.DEBUG,
    "Information": logging.INFO,
    "Warning": logging.WARNING,
    "Error": logging.ERROR,
    "Critical": logging.CRITICAL,
    "None": logging.CRITICAL + 10,
}


def logging_setup(
    environ: Mapping[str, str],
    file_path: str | None = None,
    provider_factory: Callable[[str | None, str], LoggerProvider] | None = None,
) -> logging.Logger:
    """Configure and return the `daily_tasks` hierarchy logger without touching `stdout`.

    Supports dynamic log-level alteration via `DAILY_TASKS_LOG_LEVEL` (default `Debug`) or runtime
    `logger.setLevel(...)`. Sink exceptions are contained locally so telemetry failures never alter
    business outcomes.
    """
    nyssa_level = str(parse_log_level(environ.get(LOG_LEVEL_ENV_VAR) or "Debug"))
    py_level = _PYTHON_LEVELS.get(nyssa_level, logging.DEBUG)
    sink_level = "None" if nyssa_level == "None" else "Trace"
    factory = (
        provider_factory(file_path, sink_level)
        if provider_factory is not None
        else create_nyssa_logging(file_path, sink_level)
    )

    class _NyssaBridgeHandler(logging.Handler):
        """Bridge stdlib `logging.LogRecord` events into `nyssa_ai_logging` with sink failure containment."""

        def __init__(self) -> None:
            super().__init__(level=logging.NOTSET)
            setattr(self, _HANDLER_MARKER, True)
            self.lost_records = 0

        def emit(self, record: logging.LogRecord) -> None:
            try:
                sink_logger = factory.create_logger(record.name)
                raw_fields = record.__dict__.get("fields")
                fields = dict(raw_fields) if isinstance(raw_fields, Mapping) else None
                raw_op = record.__dict__.get("operation")
                operation = str(raw_op) if isinstance(raw_op, str) else ""
                raw_err = record.__dict__.get("error")
                exc_err = record.exc_info[1] if record.exc_info and record.exc_info[1] is not None else None
                err = raw_err if isinstance(raw_err, BaseException) else exc_err
                msg = record.getMessage()
                if record.levelno >= logging.ERROR:
                    sink_logger.error(msg, error=err, fields=fields, operation=operation)
                elif record.levelno >= logging.WARNING:
                    sink_logger.warn(msg, fields=fields, operation=operation)
                elif record.levelno >= logging.INFO:
                    sink_logger.info(msg, fields=fields, operation=operation)
                else:
                    sink_logger.debug(msg, fields=fields, operation=operation)
            except Exception:
                self.lost_records += 1

    package_logger = logging.getLogger(_PACKAGE_LOGGER_NAME)
    package_logger.setLevel(py_level)
    package_logger.propagate = False
    for existing in list(package_logger.handlers):
        if getattr(existing, _HANDLER_MARKER, False):
            package_logger.removeHandler(existing)
    package_logger.addHandler(_NyssaBridgeHandler())
    return package_logger
