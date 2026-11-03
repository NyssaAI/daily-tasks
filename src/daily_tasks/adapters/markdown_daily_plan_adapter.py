# Responsibility: Read the daily plans nearest a local date from a folder of daily plan Markdown files.
# Public interface:
# `-- MarkdownDailyPlanAdapter
#     +-- fetch_plans(around)
#     +-- name
#     `-- new(root, name, logger)
"""File-backed Daily-Plan-Port: `<root>/YYYY.MM.DD-daily-plan.md` records parsed through the CST."""

import asyncio
import os
import re
import time
from datetime import date
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Ok, Result, fail, ok

from daily_tasks.domain import DailyPlan
from daily_tasks.ports import PortLogger
from daily_tasks.storage.cst import RecordLocation, parse_daily_plan, parse_markdown

_OPERATION: Final = "daily_plan.fetch"
_PLAN_FILE: Final = re.compile(r"^(\d{4})\.(\d{2})\.(\d{2})-daily-plan\.md$")


@final
class MarkdownDailyPlanAdapter:
    """Daily plan source backed by one folder of `YYYY.MM.DD-daily-plan.md` files.

    Plan paths are `<root folder name>/<file name>` (for example `daily-plans/2026.11.03-daily-plan.md`);
    their `source` is `name`.
    """

    def __init__(self, root: Path, name: str, logger: PortLogger) -> None:
        """Borrow `logger`; `root` must be absolute so results never depend on the working directory."""
        if not root.is_absolute():
            raise ValueError("daily plans root must be an absolute path")
        self._root = root
        self._name = name
        self._logger = logger

    @property
    def name(self) -> str:
        """Configured source name."""
        return self._name

    async def fetch_plans(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        """Return the plan dated `around` (when present) and the latest earlier plan, newest first.

        A file whose name or content is malformed is skipped with a warning and the next earlier
        plan is used. Fails with `NotFound` when the root does not exist and `Unavailable` when it
        cannot be listed.
        """
        return await asyncio.to_thread(self._read, around)

    def _read(self, around: date) -> Result[tuple[DailyPlan, ...]]:
        started = time.monotonic()
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
        self._logger.info(
            "daily plans fetched", fields={**fields, "elapsed_ms": _elapsed_ms(started)}, operation=_OPERATION
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
        self._logger.warn("daily plan skipped", fields=fields, operation=_OPERATION)

    def _fail(
        self, message: str, category: ErrorCategory, error: OSError, started: float
    ) -> Result[tuple[DailyPlan, ...]]:
        fields = {"source": self._name, "category": str(category), "elapsed_ms": _elapsed_ms(started)}
        self._logger.error(message, error=error, fields=fields, operation=_OPERATION)
        return fail(f"Daily plan source '{self._name}': {message}.", category, cause=error)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
