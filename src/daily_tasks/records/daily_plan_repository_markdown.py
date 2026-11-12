"""Responsibility: Read the daily plans nearest a local date from a folder of daily plan Markdown files.
Public interface:
`-- DailyPlanRepositoryMarkdown
    +-- fetch_plans(around)
    +-- malformed_records
    +-- name
    `-- new(root, name)
"""

import asyncio
import logging
import os
import re
import time
from datetime import date
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Ok, Result, fail, ok

from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.types import MalformedRecord, RecordLocation
from daily_tasks.records.cst.parse_daily_plan import parse_daily_plan
from daily_tasks.records.cst.parse_markdown import parse_markdown

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "daily_plan.fetch"
_PLAN_FILE: Final = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})-daily-plan\.md$")


@final
class DailyPlanRepositoryMarkdown:
    """Entity-first Markdown implementation of `DailyPlanRepository`."""

    def __init__(self, root: Path, name: str) -> None:
        """`root` must be absolute so results never depend on the working directory."""
        if not root.is_absolute():
            raise ValueError("daily plans root must be an absolute path")
        self._root = root
        self._name = name
        self._malformed_records: list[MalformedRecord] = []

    @property
    def name(self) -> str:
        """Configured repository name."""
        return self._name

    @property
    def malformed_records(self) -> tuple[MalformedRecord, ...]:
        """Malformed or unreadable daily plans skipped during the most recent fetch."""
        return tuple(self._malformed_records)

    async def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        """Return the plan dated `around` (when present) and the latest earlier plan, newest first."""
        return await asyncio.to_thread(self._read, around)

    def _read(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        started = time.monotonic()
        self._malformed_records = []
        try:
            with os.scandir(self._root) as entries:
                names = [entry.name for entry in entries if entry.is_file()]
        except (FileNotFoundError, NotADirectoryError) as error:
            return self._fail("daily plans root not found", ErrorCategory.NOT_FOUND, error, started)
        except OSError as error:
            return self._fail("daily plans root unreadable", ErrorCategory.UNAVAILABLE, error, started)
        dated = sorted(((d, n) for n in names if (d := self._date_of(n)) is not None and d <= around), reverse=True)
        plans: list[DailyPlan] = []
        for local_date, file_name in dated:
            plan = self._parse(file_name)
            if plan is None:
                continue
            plans.append(plan)
            if local_date < around:
                break
        fields = {"source": self._name, "around": around.isoformat(), "plans": len(plans)}
        _LOGGER.info(
            "daily plans fetched",
            extra={"operation": _OPERATION, "fields": {**fields, "elapsed_ms": _elapsed_ms(started)}},
        )
        return ok(tuple(plans))

    def _date_of(self, file_name: str) -> date | None:
        match = _PLAN_FILE.match(file_name)
        if match is None:
            return None
        try:
            return date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
        except ValueError:
            self._skip(file_name, "invalid-date", "file name is not a calendar date")
            return None

    def _parse(self, file_name: str) -> DailyPlan | None:
        try:
            with (self._root / file_name).open(encoding="utf-8", newline="") as file:
                text = file.read()
        except (OSError, UnicodeDecodeError) as error:
            self._skip(file_name, "unreadable-record", type(error).__name__)
            return None
        document = parse_markdown(text)
        if not isinstance(document, Ok):
            self._skip(file_name, document.error.code, document.error.message)
            return None
        location = RecordLocation(path=f"{self._root.name}/{file_name}", source=self._name)
        parsed = parse_daily_plan(document.value, location)
        if not isinstance(parsed, Ok):
            self._skip(file_name, parsed.error.code, parsed.error.message)
            return None
        return parsed.value.plan

    def _skip(self, file_name: str, code: str, detail: str) -> None:
        fields = {"source": self._name, "path": file_name, "code": code, "detail": detail[:200]}
        _LOGGER.warning("daily plan skipped", extra={"operation": _OPERATION, "fields": fields})
        self._malformed_records.append(
            MalformedRecord(path=f"{self._root.name}/{file_name}", kind="daily-plan", code=code, message=detail[:200])
        )

    def _fail(
        self, message: str, category: ErrorCategory, error: OSError, started: float
    ) -> Result[tuple[DailyPlan, ...]]:
        fields = {"source": self._name, "category": str(category), "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.error(message, extra={"operation": _OPERATION, "fields": fields, "error": error})
        return fail(f"Daily plan repository '{self._name}': {message}.", category, cause=error)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
