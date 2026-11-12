"""Responsibility: Load and atomically append adjudicated decisions in runtime_root.
Public interface:
`-- DecisionLogStoreJson
    +-- FILE_NAME
    +-- append_decisions(entries)
    +-- load()
    +-- new(runtime_root, vault_root)
    `-- path
"""

import logging
import os
import tempfile
import time
from collections.abc import Sequence
from dataclasses import replace
from pathlib import Path
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.core.planning.decision_log import DecisionLog
from daily_tasks.core.planning.decision_log_entry import DecisionLogEntry

_LOGGER: Final = logging.getLogger(__name__)
_DECISION_LOG: Final[TypeAdapter[DecisionLog]] = TypeAdapter(DecisionLog)
_OPERATION: Final = "decision_log.append"


@final
class DecisionLogStoreJson:
    """Entity-first JSON decision log store at `<runtime_root>/decision-log.json`."""

    FILE_NAME: ClassVar[str] = "decision-log.json"

    def __init__(self, runtime_root: Path, vault_root: str) -> None:
        """`runtime_root` must be an absolute path."""
        if not runtime_root.is_absolute():
            raise ValueError("runtime_root must be absolute")
        self._path = runtime_root / self.FILE_NAME
        self._vault_root = vault_root

    @property
    def path(self) -> Path:
        """Absolute path of `decision-log.json`."""
        return self._path

    def load(self) -> Result[DecisionLog]:
        """Load the stored decision log, or an empty `DecisionLog` when absent."""
        try:
            if not self._path.exists():
                return ok(DecisionLog(vault_root=self._vault_root, entries=()))
            return ok(_DECISION_LOG.validate_json(self._path.read_bytes()))
        except ValidationError:
            return fail("Stored decision log is malformed.", "Validation")
        except OSError as exc:
            return fail(f"Decision log could not be read: '{self._path}'.", "Unavailable", cause=exc)

    def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]:
        """Append `entries` atomically after any stored entries."""
        started = time.monotonic()
        loaded = self.load()
        if not loaded.ok:
            return fail(loaded.message, loaded.category)
        updated = replace(loaded.value, entries=(*loaded.value.entries, *entries))
        payload = _DECISION_LOG.dump_json(updated, by_alias=True, indent=2) + b"\n"
        temp_name: str | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self._path.parent, prefix=".decision-log.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self._path)
        except OSError as exc:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            _LOGGER.error("decision log write failed", extra={"operation": _OPERATION, "error": exc})
            return fail(f"Decision log could not be written: '{self._path}'.", "Unavailable", cause=exc)
        _LOGGER.info(
            "decision log updated",
            extra={
                "operation": _OPERATION,
                "fields": {"appended": len(entries), "elapsed_ms": round((time.monotonic() - started) * 1000, 3)},
            },
        )
        return ok(None)
