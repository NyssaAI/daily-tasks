"""Responsibility: Load and atomically save communication suggestions in runtime_root.
Public interface:
`-- SuggestionsRepositoryJson
    +-- FILE_NAME
    +-- load()
    +-- new(runtime_root, vault_root, clock)
    +-- path
    `-- save(suggestions)
"""

import logging
import os
import tempfile
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.core.communications.suggestions import Suggestions

_LOGGER: Final = logging.getLogger(__name__)
_SUGGESTIONS: Final[TypeAdapter[Suggestions]] = TypeAdapter(Suggestions)
_LOAD: Final = "suggestions.load"
_SAVE: Final = "suggestions.save"


@final
class SuggestionsRepositoryJson:
    """Entity-first JSON implementation of `SuggestionsRepository` at `<runtime_root>/suggestions.json`."""

    FILE_NAME: ClassVar[str] = "suggestions.json"

    def __init__(self, runtime_root: Path, vault_root: str, clock: Callable[[], datetime]) -> None:
        """`runtime_root` must be an absolute path."""
        if not runtime_root.is_absolute():
            raise ValueError("runtime_root must be absolute so suggestions do not depend on the working directory")
        self._path = runtime_root / self.FILE_NAME
        self._vault_root = vault_root
        self._clock = clock

    @property
    def path(self) -> Path:
        """Absolute path of the suggestions file."""
        return self._path

    def load(self) -> Result[Suggestions]:
        """Return saved suggestions, or empty suggestions when the file does not exist."""
        started = time.monotonic()
        try:
            raw = self._path.read_bytes()
        except FileNotFoundError:
            return ok(
                Suggestions(
                    vault_root=self._vault_root,
                    updated_at=self._clock(),
                    no_suggestion_message_ids=(),
                    suggestions=(),
                )
            )
        except OSError as exc:
            _LOGGER.error("suggestions unreadable", extra={"operation": _LOAD, "error": exc})
            return fail("Suggestions could not be read.", "Unavailable", cause=exc)
        try:
            loaded = _SUGGESTIONS.validate_json(raw)
        except ValidationError as exc:
            _LOGGER.error("suggestions malformed", extra={"operation": _LOAD, "fields": {"errors": exc.error_count()}})
            return fail(f"Suggestions file '{self._path}' is malformed.", "Validation", cause=exc)
        _LOGGER.info(
            "suggestions loaded",
            extra={
                "operation": _LOAD,
                "fields": {
                    "count": len(loaded.suggestions),
                    "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
                },
            },
        )
        return ok(loaded)

    def save(self, suggestions: Suggestions) -> Result[None]:
        """Replace `suggestions.json` atomically."""
        started = time.monotonic()
        payload = _SUGGESTIONS.dump_json(suggestions, by_alias=True, indent=2) + b"\n"
        temp_name: str | None = None
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=self._path.parent, prefix=".suggestions.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, self._path)
        except OSError as exc:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            _LOGGER.error("suggestions not saved", extra={"operation": _SAVE, "error": exc})
            return fail("Suggestions could not be saved.", "Unavailable", cause=exc)
        _LOGGER.info(
            "suggestions saved",
            extra={
                "operation": _SAVE,
                "fields": {
                    "count": len(suggestions.suggestions),
                    "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
                },
            },
        )
        return ok(None)
