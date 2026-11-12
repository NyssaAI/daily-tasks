"""Responsibility: Load and atomically save the per-source fetch cursors of one vault in runtime_root.
Public interface:
`-- CursorStoreJson
    +-- FILE_NAME
    +-- load()
    +-- new(runtime_root, vault_root)
    +-- path
    `-- save(cursors)
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.core.communications.fetch_cursors import FetchCursors

_LOGGER: Final = logging.getLogger(__name__)
_CURSORS: Final[TypeAdapter[FetchCursors]] = TypeAdapter(FetchCursors)
_LOAD: Final = "cursors.load"
_SAVE: Final = "cursors.save"


@final
class CursorStoreJson:
    """Entity-first JSON implementation of `CursorStore` at `<runtime_root>/fetch-cursors.json`."""

    FILE_NAME: ClassVar[str] = "fetch-cursors.json"

    def __init__(self, runtime_root: Path, vault_root: str) -> None:
        """`runtime_root` must be an absolute path so cursors do not depend on the working directory."""
        if not runtime_root.is_absolute():
            raise ValueError("runtime_root must be absolute so cursors do not depend on the working directory")
        self._path = runtime_root / self.FILE_NAME
        self._vault_root = vault_root

    @property
    def path(self) -> Path:
        """Absolute path of the cursor file."""
        return self._path

    def load(self) -> Result[FetchCursors]:
        """Return the saved cursors, or empty cursors for the vault when the file does not exist."""
        started = time.monotonic()
        try:
            raw = self._path.read_bytes()
        except FileNotFoundError:
            _LOGGER.info(
                "cursors missing; starting empty",
                extra={"operation": _LOAD, "fields": self._fields(started, 0)},
            )
            return ok(FetchCursors(vault_root=self._vault_root, cursors={}))
        except OSError as exc:
            _LOGGER.error(
                "cursors unreadable",
                extra={"operation": _LOAD, "fields": self._fields(started, 0), "error": exc},
            )
            return fail("Fetch cursors could not be read.", "Unavailable", cause=exc)
        try:
            cursors = _CURSORS.validate_json(raw)
        except ValidationError as exc:
            fields = {**self._fields(started, 0), "error_count": exc.error_count()}
            _LOGGER.error("cursors malformed", extra={"operation": _LOAD, "fields": fields})
            return fail(f"Fetch cursors file '{self._path}' is malformed.", "Validation", cause=exc)
        _LOGGER.info(
            "cursors loaded",
            extra={"operation": _LOAD, "fields": self._fields(started, len(cursors.cursors))},
        )
        return ok(cursors)

    def save(self, cursors: FetchCursors) -> Result[None]:
        """Replace the cursor file atomically; on failure the previous file is left unchanged."""
        started = time.monotonic()
        payload = _CURSORS.dump_json(cursors, by_alias=True, indent=2) + b"\n"
        temp_name: str | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self._path.parent, prefix=".fetch-cursors.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self._path)
        except OSError as exc:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            _LOGGER.error(
                "cursors not saved",
                extra={"operation": _SAVE, "fields": self._fields(started, 0), "error": exc},
            )
            return fail("Fetch cursors could not be saved.", "Unavailable", cause=exc)
        _LOGGER.info(
            "cursors saved",
            extra={"operation": _SAVE, "fields": self._fields(started, len(cursors.cursors))},
        )
        return ok(None)

    def _fields(self, started: float, sources: int) -> dict[str, object]:
        return {
            "path": str(self._path),
            "sources": sources,
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        }
