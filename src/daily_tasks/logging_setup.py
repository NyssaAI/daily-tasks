# Responsibility: Build the structured logger the MCP server writes to standard error.
# Public interface:
# +-- LOG_LEVEL_ENV_VAR
# `-- logging_setup(category, environ, file_path)
"""`nyssa-ai-logging` composition: stderr always (stdout stays JSON-RPC only), plus an optional JSON file."""

from collections.abc import Mapping
from typing import Final

from nyssa_ai_logging import (  # type: ignore[import-untyped]  # package ships no py.typed
    create_nyssa_logging,
    parse_log_level,
)

from daily_tasks.ports import PortLogger

LOG_LEVEL_ENV_VAR: Final = "DAILY_TASKS_LOG_LEVEL"


def logging_setup(category: str, environ: Mapping[str, str], file_path: str | None = None) -> PortLogger:
    """Return a logger for `category`; the level comes from `DAILY_TASKS_LOG_LEVEL` (default Information).

    Never writes to stdout.
    """
    level = parse_log_level(environ.get(LOG_LEVEL_ENV_VAR) or "Information")
    logger: PortLogger = create_nyssa_logging(file_path, level).create_logger(category)
    return logger
