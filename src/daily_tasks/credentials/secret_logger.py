# Responsibility: Define the structured log calls secret resolution needs from its logger.
# Public interface:
# `-- SecretLogger
#     +-- debug(message, fields, operation)
#     +-- error(message, error, fields, operation)
#     `-- warn(message, fields, operation)
"""Narrow logger contract; `nyssa_ai_logging.Logger` satisfies it structurally."""

from collections.abc import Mapping
from typing import Protocol


class SecretLogger(Protocol):
    """Structured logger; callers never pass secret values in `message` or `fields`."""

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        """Log step telemetry."""
        ...

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        """Log a recoverable degradation."""
        ...

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        """Log a failed operational boundary outcome."""
        ...
