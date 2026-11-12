"""Responsibility: Read project, milestone, task, and blocker records from a Markdown project vault.
Public interface:
`-- ProjectPlanRepositoryMarkdown
    +-- fetch_projects()
    +-- malformed_records
    +-- name
    `-- new(root, name)
"""

import asyncio
import logging
import time
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Ok, Result, fail, ok

from daily_tasks.core.records.blocker import Blocker
from daily_tasks.core.records.milestone import Milestone
from daily_tasks.core.records.project import Project
from daily_tasks.core.records.record_kind import RecordKind
from daily_tasks.core.records.task import Task
from daily_tasks.core.records.types import MalformedRecord, ProjectPlanSnapshot, RecordLocation
from daily_tasks.records.cst.markdown_document import MarkdownDocument
from daily_tasks.records.cst.parse_blocker import parse_blocker
from daily_tasks.records.cst.parse_error import ParseError
from daily_tasks.records.cst.parse_markdown import parse_markdown
from daily_tasks.records.cst.parse_milestone import parse_milestone
from daily_tasks.records.cst.parse_project import parse_project
from daily_tasks.records.cst.parse_task import parse_task
from daily_tasks.records.markdown_record_files import markdown_record_files
from daily_tasks.records.markdown_record_kind import markdown_record_kind

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "project_plan.fetch"

type _Record = Project | Milestone | Task | Blocker
type _Parser = Callable[[MarkdownDocument, RecordLocation], Result[_Record, ParseError]]

_PARSERS: Final[Mapping[RecordKind, _Parser]] = {
    "project": parse_project,
    "milestone": parse_milestone,
    "task": parse_task,
    "blocker": parse_blocker,
}
_ORDER: Final[tuple[RecordKind, ...]] = ("project", "milestone", "task", "blocker")


@final
class ProjectPlanRepositoryMarkdown:
    """Entity-first Markdown implementation of `ProjectPlanRepository`."""

    def __init__(self, root: Path, name: str) -> None:
        """`root` must be absolute so results never depend on the working directory."""
        if not root.is_absolute():
            raise ValueError("projects root must be an absolute path")
        self._root = root
        self._name = name
        self._malformed_records: list[MalformedRecord] = []

    @property
    def name(self) -> str:
        """Configured repository name."""
        return self._name

    @property
    def malformed_records(self) -> tuple[MalformedRecord, ...]:
        """Malformed or unreadable records skipped during the most recent fetch."""
        return tuple(self._malformed_records)

    async def fetch_projects(self) -> Result[ProjectPlanSnapshot]:
        """Return every parseable record below the root."""
        return await asyncio.to_thread(self._read)

    def _read(self) -> Result[ProjectPlanSnapshot]:
        started = time.monotonic()
        self._malformed_records = []
        try:
            paths = markdown_record_files(self._root)
        except (FileNotFoundError, NotADirectoryError) as error:
            return self._fail("projects root not found", ErrorCategory.NOT_FOUND, error, started)
        except OSError as error:
            return self._fail("projects root unreadable", ErrorCategory.UNAVAILABLE, error, started)
        records: dict[RecordKind, list[_Record]] = {kind: [] for kind in _ORDER}
        owners: dict[PurePosixPath, str] = {}
        classified = [(kind, path) for path in paths if (kind := markdown_record_kind(path)) is not None]
        skipped = 0
        for kind in _ORDER:
            for path in (p for k, p in classified if k == kind):
                record = self._parse(kind, path, owners)
                if record is None:
                    skipped += 1
                    continue
                records[kind].append(record)
                if kind in ("project", "milestone"):
                    owners[path.parent] = record.owner
        snapshot = ProjectPlanSnapshot(
            projects=tuple(r for r in records["project"] if isinstance(r, Project)),
            milestones=tuple(r for r in records["milestone"] if isinstance(r, Milestone)),
            tasks=tuple(r for r in records["task"] if isinstance(r, Task)),
            blockers=tuple(r for r in records["blocker"] if isinstance(r, Blocker)),
            malformed_records=tuple(self._malformed_records),
        )
        fields: dict[str, object] = {kind: len(records[kind]) for kind in _ORDER}
        out_fields = {"source": self._name, **fields, "skipped": skipped, "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.info("project plan fetched", extra={"operation": _OPERATION, "fields": out_fields})
        return ok(snapshot)

    def _parse(self, kind: RecordKind, path: PurePosixPath, owners: Mapping[PurePosixPath, str]) -> _Record | None:
        try:
            with (self._root / path).open(encoding="utf-8", newline="") as file:
                text = file.read()
        except (OSError, UnicodeDecodeError) as error:
            self._skip(path, kind, "unreadable-record", type(error).__name__)
            return None
        document = parse_markdown(text)
        if not isinstance(document, Ok):
            self._skip(path, kind, document.error.code, document.error.message)
            return None
        inherited = next((owners[p] for p in path.parents if p in owners), None)
        location = RecordLocation(path=path.as_posix(), source=self._name, inherited_owner=inherited)
        record = _PARSERS[kind](document.value, location)
        if not isinstance(record, Ok):
            self._skip(path, kind, record.error.code, record.error.message)
            return None
        return record.value

    def _skip(self, path: PurePosixPath, kind: RecordKind, code: str, detail: str) -> None:
        fields = {"source": self._name, "path": path.as_posix(), "kind": kind, "code": code, "detail": detail[:200]}
        _LOGGER.warning("record skipped", extra={"operation": _OPERATION, "fields": fields})
        self._malformed_records.append(
            MalformedRecord(path=path.as_posix(), kind=kind, code=code, message=detail[:200])
        )

    def _fail(
        self, message: str, category: ErrorCategory, error: OSError, started: float
    ) -> Result[ProjectPlanSnapshot]:
        fields = {"source": self._name, "category": str(category), "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.error(message, extra={"operation": _OPERATION, "fields": fields, "error": error})
        return fail(f"Project plan repository '{self._name}': {message}.", category, cause=error)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
