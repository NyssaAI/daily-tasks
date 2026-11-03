# Responsibility: Define the structured log calls port adapters and planning services need from their logger.
# Public interface:
# `-- PortLogger
#     +-- debug(message, fields, operation)
#     +-- error(message, error, fields, operation)
#     +-- info(message, fields, operation)
#     `-- warn(message, fields, operation)
"""Narrow logger contract; `nyssa_ai_logging.Logger` satisfies it structurally."""

from collections.abc import Mapping
from typing import Protocol


class PortLogger(Protocol):
    """Structured logger; callers never pass secrets or message bodies in `message` or `fields`."""

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        """Log step telemetry."""
        ...

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        """Log a routine boundary outcome."""
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
