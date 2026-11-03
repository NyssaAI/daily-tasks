# Responsibility: Read project, milestone, task and blocker records from a Markdown project vault.
# Public interface:
# `-- MarkdownProjectPlanAdapter
#     +-- fetch_projects()
#     +-- malformed_records
#     +-- name
#     `-- new(root, name, logger)
"""File-backed Project-Plan-Port: Markdown records under one projects root, parsed through the CST."""

import asyncio
import time
from collections.abc import Callable, Mapping
from pathlib import Path, PurePosixPath
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Ok, Result, fail, ok

from daily_tasks.adapters.markdown_record_files import markdown_record_files
from daily_tasks.adapters.markdown_record_kind import MarkdownRecordKind, markdown_record_kind
from daily_tasks.domain import Blocker, Milestone, Project, Task
from daily_tasks.ports import MalformedRecord, PortLogger, ProjectPlanSnapshot
from daily_tasks.storage.cst import (
    MarkdownDocument,
    ParseError,
    RecordLocation,
    parse_blocker,
    parse_markdown,
    parse_milestone,
    parse_project,
    parse_task,
)

_OPERATION: Final = "project_plan.fetch"

type _Record = Project | Milestone | Task | Blocker
type _Parser = Callable[[MarkdownDocument, RecordLocation], Result[_Record, ParseError]]

_PARSERS: Final[Mapping[MarkdownRecordKind, _Parser]] = {
    "project": parse_project,
    "milestone": parse_milestone,
    "task": parse_task,
    "blocker": parse_blocker,
}
_ORDER: Final[tuple[MarkdownRecordKind, ...]] = ("project", "milestone", "task", "blocker")


@final
class MarkdownProjectPlanAdapter:
    """Project plan source backed by `<root>/<YYYY.MM.DD-project>/...` Markdown records.

    Records without an `owner` inherit the owner of their milestone, else of their project. Record
    paths are relative to `root`; their `source` is `name`.
    """

    def __init__(self, root: Path, name: str, logger: PortLogger) -> None:
        """Borrow `logger`; `root` must be absolute so results never depend on the working directory."""
        if not root.is_absolute():
            raise ValueError("projects root must be an absolute path")
        self._root = root
        self._name = name
        self._logger = logger
        self._malformed_records: list[MalformedRecord] = []

    @property
    def name(self) -> str:
        """Configured source name."""
        return self._name

    @property
    def malformed_records(self) -> tuple[MalformedRecord, ...]:
        """Malformed or unreadable records skipped during the most recent fetch."""
        return tuple(self._malformed_records)

    async def fetch_projects(self) -> Result[ProjectPlanSnapshot]:
        """Return every parseable record below the root.

        Malformed or unreadable records are skipped with a warning and recorded in `malformed_records`.
        Fails with `NotFound` when the root does not exist and `Unavailable` when it cannot be listed.
        """
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
        records: dict[MarkdownRecordKind, list[_Record]] = {kind: [] for kind in _ORDER}
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
        self._logger.info(
            "project plan fetched",
            fields={"source": self._name, **fields, "skipped": skipped, "elapsed_ms": _elapsed_ms(started)},
            operation=_OPERATION,
        )
        return ok(snapshot)

    def _parse(
        self, kind: MarkdownRecordKind, path: PurePosixPath, owners: Mapping[PurePosixPath, str]
    ) -> _Record | None:
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

    def _skip(self, path: PurePosixPath, kind: str, code: str, detail: str) -> None:
        fields = {"source": self._name, "path": path.as_posix(), "kind": kind, "code": code, "detail": detail[:200]}
        self._logger.warn("record skipped", fields=fields, operation=_OPERATION)
        self._malformed_records.append(
            MalformedRecord(path=path.as_posix(), kind=kind, code=code, message=detail[:200])
        )

    def _fail(
        self, message: str, category: ErrorCategory, error: OSError, started: float
    ) -> Result[ProjectPlanSnapshot]:
        fields = {"source": self._name, "category": str(category), "elapsed_ms": _elapsed_ms(started)}
        self._logger.error(message, error=error, fields=fields, operation=_OPERATION)
        return fail(f"Project plan source '{self._name}': {message}.", category, cause=error)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
