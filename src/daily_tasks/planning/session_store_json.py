"""Responsibility: Atomically persist confirmed planning session snapshots in runtime_root.
Public interface:
`-- SessionStoreJson
    +-- new(runtime_root)
    `-- save_session(session)
"""

import logging
import os
import tempfile
import time
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter

from daily_tasks.core.planning.planning_session import PlanningSession

_LOGGER: Final = logging.getLogger(__name__)
_SESSION: Final[TypeAdapter[PlanningSession]] = TypeAdapter(PlanningSession)
_OPERATION: Final = "session.save"


@final
class SessionStoreJson:
    """Entity-first JSON session store at `<runtime_root>/sessions/YYYY.MM.DD.json`."""

    def __init__(self, runtime_root: Path) -> None:
        """`runtime_root` must be an absolute path."""
        if not runtime_root.is_absolute():
            raise ValueError("runtime_root must be absolute")
        self._sessions_dir = runtime_root / "sessions"

    def save_session(self, session: PlanningSession) -> Result[None]:
        """Write `sessions/YYYY.MM.DD.json` atomically."""
        started = time.monotonic()
        target = self._sessions_dir / f"{session.local_date.strftime('%Y.%m.%d')}.json"
        payload = _SESSION.dump_json(session, by_alias=True, indent=2) + b"\n"
        temp_name: str | None = None
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            with tempfile.NamedTemporaryFile(
                mode="wb", dir=target.parent, prefix=".session.", suffix=".tmp", delete=False
            ) as handle:
                temp_name = handle.name
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(temp_name, target)
        except OSError as exc:
            if temp_name is not None:
                Path(temp_name).unlink(missing_ok=True)
            _LOGGER.error("session save failed", extra={"operation": _OPERATION, "error": exc})
            return fail(f"Session file could not be written: '{target}'.", "Unavailable", cause=exc)
        _LOGGER.info(
            "session saved",
            extra={
                "operation": _OPERATION,
                "fields": {"path": str(target), "elapsed_ms": round((time.monotonic() - started) * 1000, 3)},
            },
        )
        return ok(None)
