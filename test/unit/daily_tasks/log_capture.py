"""Responsibility: Define the in-memory structured log capture container for unit tests.
Public interface:
`-- LogCapture
    +-- operations
    `-- records
"""

from collections.abc import Mapping
from dataclasses import dataclass, field


@dataclass
class LogCapture:
    """In-memory sink for structured log records emitted under `daily_tasks`."""

    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)
    operations: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)
