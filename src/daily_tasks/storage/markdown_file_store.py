"""Responsibility: Persist adjudicated record changes, daily plans and planning state as local files.
Public interface:
`-- MarkdownFileStore
    +-- append_decisions(entries)
    +-- apply(changes)
    +-- new(workspace_root, clock, records_root, daily_plans_root, state_root)
    +-- save_session(session)
    +-- save_suggestions(suggestions)
    `-- write_daily_plan(document)

Markdown `LocalFileStore`: optimistic hash checks, surgical record edits and atomic writes.
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
from pydantic import TypeAdapter, ValidationError

from daily_tasks.domain import DecisionLog, DecisionLogEntry, PlanningSession, RecordChange, Suggestions
from daily_tasks.storage.apply_record_change import apply_record_change
from daily_tasks.storage.atomic_write import atomic_write
from daily_tasks.storage.cst import DailyPlanDocument, render_daily_plan

_LOGGER: Final = logging.getLogger(__name__)
_DECISION_LOG: Final[TypeAdapter[DecisionLog]] = TypeAdapter(DecisionLog)
_SESSION: Final[TypeAdapter[PlanningSession]] = TypeAdapter(PlanningSession)
_SUGGESTIONS: Final[TypeAdapter[Suggestions]] = TypeAdapter(Suggestions)


def _hash(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)


@final
class MarkdownFileStore:
    """The only writer of records and `.nyssa-ai/daily-tasks/` state; callers pass adjudicated input only.

    Record change paths are relative to `records_root` (as in `task.json`); every root resolves
    against the absolute `workspace_root`, never the working directory.
    """

    def __init__(
        self,
        workspace_root: Path,
        clock: Callable[[], datetime],
        records_root: Path = Path("projects"),
        daily_plans_root: Path = Path("daily-plans"),
        state_root: Path = Path(".nyssa-ai/daily-tasks"),
    ) -> None:
        """`clock` returns the UTC time stamped on applied changes.

        Raises `ValueError` when `workspace_root` is relative.
        """
        if not workspace_root.is_absolute():
            raise ValueError("workspace_root must be an absolute path")
        self._workspace_root = workspace_root
        self._records_root = workspace_root / records_root
        self._daily_plans_root = workspace_root / daily_plans_root
        self._state_root = workspace_root / state_root
        self._clock = clock

    def apply(self, changes: Sequence[RecordChange]) -> Result[tuple[RecordChange, ...]]:
        """Verify every `expected_hash`, compute every new text, then write each touched file atomically.

        Hashes are compared with the file bytes read before any edit. Fails before writing with
        `Conflict` (hash mismatch), `NotFound` (missing record), `Validation` (path outside the records
        root or a change that cannot be applied in place) or `Unavailable` (read failure). A failed write
        restores already-replaced files and fails with `Unavailable`.
        """
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

    def save_suggestions(self, suggestions: Suggestions) -> Result[None]:
        """Replace `suggestions.json`; fails with `Unavailable` on I/O failure."""
        data = _SUGGESTIONS.dump_json(suggestions, by_alias=True, indent=2).decode("utf-8")
        written = self._write("file_store.save_suggestions", self._state_root / "suggestions.json", data)
        return ok(None) if isinstance(written, Ok) else written

    def append_decisions(self, entries: Sequence[DecisionLogEntry]) -> Result[None]:
        """Append `entries` after the stored ones, which are kept in order and unchanged.

        Fails with `Validation` when the stored log is malformed or `Unavailable` on I/O failure.
        """
        started = time.monotonic()
        operation = "file_store.append_decisions"
        path = self._state_root / "decision-log.json"
        try:
            stored = _DECISION_LOG.validate_json(path.read_bytes()) if path.exists() else None
        except ValidationError:
            return self._refuse(operation, started, "Stored decision log is malformed.")
        except OSError as error:
            return self._io_failure(operation, started, error, self._relative(path))
        log = stored or DecisionLog(workspace_root=self._workspace_root.as_posix(), entries=())
        updated = replace(log, entries=(*log.entries, *entries))
        data = _DECISION_LOG.dump_json(updated, by_alias=True, indent=2).decode("utf-8")
        written = self._write(operation, path, data, {"appended": len(entries)})
        return ok(None) if isinstance(written, Ok) else written

    def save_session(self, session: PlanningSession) -> Result[None]:
        """Replace `sessions/YYYY.MM.DD.json` for the session's local date; fails with `Unavailable`."""
        path = self._state_root / "sessions" / f"{session.local_date.strftime('%Y.%m.%d')}.json"
        data = _SESSION.dump_json(session, by_alias=True, indent=2).decode("utf-8")
        written = self._write("file_store.save_session", path, data)
        return ok(None) if isinstance(written, Ok) else written

    def _record_path(self, relative: str) -> Path | None:
        path = (self._records_root / relative).resolve()
        return path if path.is_relative_to(self._records_root.resolve()) and path.suffix == ".md" else None

    def _relative(self, path: Path) -> str:
        return path.relative_to(self._workspace_root).as_posix()

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
