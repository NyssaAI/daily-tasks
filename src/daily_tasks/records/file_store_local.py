"""Responsibility: Persist adjudicated record changes and daily plans as local Markdown files inside a vault.
Public interface:
`-- FileStoreLocal
    +-- apply(changes)
    +-- new(vault_root, clock, records_root, daily_plans_root)
    `-- write_daily_plan(document)
"""

import hashlib
import logging
import time
from collections.abc import Callable, Mapping, Sequence
from dataclasses import replace
from datetime import datetime
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import Ok, Result, fail, ok

from daily_tasks.core.records.record_change import RecordChange
from daily_tasks.core.records.types import DailyPlanDocument
from daily_tasks.records.apply_record_change import apply_record_change
from daily_tasks.records.atomic_write import atomic_write
from daily_tasks.records.cst.render_daily_plan import render_daily_plan

_LOGGER: Final = logging.getLogger(__name__)


def _hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)


@final
class FileStoreLocal:
    """Entity-first local Markdown `FileStore`: optimistic hash checks, in-place record edits, and atomic writes.

    Writes strictly to vault Markdown files (`records_root` and `daily_plans_root`) and never creates `.nyssa-ai/`
    inside `vault_root`.
    """

    def __init__(
        self,
        vault_root: Path,
        clock: Callable[[], datetime],
        records_root: Path = Path("1-projects"),
        daily_plans_root: Path = Path("2-areas/daily-plans"),
    ) -> None:
        """`clock` returns the UTC time stamped on applied changes; `vault_root` must be absolute."""
        if not vault_root.is_absolute():
            raise ValueError("vault_root must be an absolute path")
        self._vault_root = vault_root
        self._records_root = records_root if records_root.is_absolute() else vault_root / records_root
        self._daily_plans_root = daily_plans_root if daily_plans_root.is_absolute() else vault_root / daily_plans_root
        self._clock = clock

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        """Verify every `expected_hash`, compute every new text, then write each touched file atomically."""
        started = time.monotonic()
        operation = "file_store.apply"
        originals: dict[Path, bytes] = {}
        pending: dict[Path, str] = {}
        names: dict[Path, str] = {}
        for change in changes:
            path = self._record_path(change.path)
            if path is None:
                return self._refuse(operation, started, f"Record path '{change.path}' is outside the records root.")
            if path not in originals:
                try:
                    originals[path] = path.read_bytes()
                except FileNotFoundError:
                    return self._refuse(operation, started, f"Record '{change.path}' does not exist.", "NotFound")
                except OSError as error:
                    return self._io_failure(operation, started, error, change.path)
            if _hash(originals[path]) != change.expected_hash:
                fields = {"path": change.path, "record_id": str(change.record_id), "elapsed_ms": _elapsed_ms(started)}
                _LOGGER.warning("record changed since it was read", extra={"operation": operation, "fields": fields})
                return fail(f"Record '{change.path}' changed since it was read.", "Conflict")
            edited = apply_record_change(pending.get(path, originals[path].decode("utf-8")), change)
            if not isinstance(edited, Ok):
                return self._refuse(operation, started, f"Record '{change.path}': {edited.error.message}")
            pending[path] = edited.value
            names[path] = change.path
        written: list[Path] = []
        try:
            for target, text in pending.items():
                atomic_write(target, text.encode("utf-8"))
                written.append(target)
        except OSError as error:
            self._restore(written, originals, names)
            return self._io_failure(operation, started, error, names[target])
        applied_at = self._clock()
        fields = {"changes": len(changes), "files": len(pending), "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.info("record changes applied", extra={"operation": operation, "fields": fields})
        return ok(tuple(replace(change, status="applied", applied_at=applied_at) for change in changes))

    def write_daily_plan(self, document: DailyPlanDocument) -> Result[str]:
        """Render and write `YYYY.MM.DD-daily-plan.md`; fails with `Unavailable` on I/O failure."""
        name = f"{document.plan.local_date.strftime('%Y.%m.%d')}-daily-plan.md"
        return self._write("file_store.write_daily_plan", self._daily_plans_root / name, render_daily_plan(document))

    def _record_path(self, relative: str) -> Path | None:
        path = (self._records_root / relative).resolve()
        return path if path.is_relative_to(self._records_root.resolve()) and path.suffix == ".md" else None

    def _relative(self, path: Path) -> str:
        if path.is_relative_to(self._vault_root):
            return path.relative_to(self._vault_root).as_posix()
        return path.as_posix()

    def _write(self, operation: str, path: Path, text: str, extra: Mapping[str, object] | None = None) -> Result[str]:
        started = time.monotonic()
        relative = self._relative(path)
        try:
            atomic_write(path, text.encode("utf-8"))
        except OSError as error:
            return self._io_failure(operation, started, error, relative)
        fields = {"path": relative, **(extra or {}), "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.info("file written", extra={"operation": operation, "fields": fields})
        return ok(relative)

    def _restore(self, written: Sequence[Path], originals: Mapping[Path, bytes], names: Mapping[Path, str]) -> None:
        for path in written:
            try:
                atomic_write(path, originals[path])
            except OSError as error:
                fields = {"path": names[path]}
                _LOGGER.error(
                    "record restore failed",
                    extra={"operation": "file_store.apply", "fields": fields, "error": error},
                )

    def _refuse[T](self, operation: str, started: float, message: str, category: str = "Validation") -> Result[T]:
        _LOGGER.warning(
            "file store refused",
            extra={"operation": operation, "fields": {"category": category, "elapsed_ms": _elapsed_ms(started)}},
        )
        return fail(message, category)

    def _io_failure[T](self, operation: str, started: float, error: OSError, target: str) -> Result[T]:
        fields = {"target": target, "error_type": type(error).__name__, "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.error("file store I/O failed", extra={"operation": operation, "fields": fields, "error": error})
        return fail(f"File store could not access '{target}'.", "Unavailable", cause=error)
