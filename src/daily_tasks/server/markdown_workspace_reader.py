# Responsibility: Read the Markdown vault and configured message sources into one planning snapshot.
# Public interface:
# `-- MarkdownWorkspaceReader
#     +-- new(settings, logger, communication, cursor_store)
#     `-- read(now)
"""Default `WorkspaceReader`: Markdown project and daily plan adapters, record hashes and an optional fetch."""

import hashlib
import time
from datetime import datetime
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import Err, Result, ok

from daily_tasks.adapters.markdown_daily_plan_adapter import MarkdownDailyPlanAdapter
from daily_tasks.adapters.markdown_project_plan_adapter import MarkdownProjectPlanAdapter
from daily_tasks.domain import DailyPlan, FetchCursors, Message, MessageSourceStatus
from daily_tasks.graph import DailyPlanSourceRead, ProjectPlanSourceRead, StateGraphSettings, build_state_graph
from daily_tasks.graph.local_date_in import local_date_in
from daily_tasks.ports import CommunicationPort, PortLogger
from daily_tasks.server.types import ServerSettings, WorkspaceSnapshot
from daily_tasks.storage.cursor_store import CursorStore

_OPERATION: Final = "workspace.read"
_PROJECTS: Final = "markdown-projects"
_PLANS: Final = "markdown-daily-plans"


def _file_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    for path in sorted(root.rglob("*.md")):
        try:
            hashes[path.relative_to(root).as_posix()] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return hashes


@final
class MarkdownWorkspaceReader:
    """Borrow `logger`, `communication` and `cursor_store`; without `communication` no message is fetched."""

    def __init__(
        self,
        settings: ServerSettings,
        logger: PortLogger,
        communication: CommunicationPort | None = None,
        cursor_store: CursorStore | None = None,
    ) -> None:
        """Keep the collaborators; nothing is read until `read`."""
        self._settings = settings
        self._logger = logger
        self._communication = communication
        self._cursor_store = cursor_store

    async def read(self, now: datetime) -> Result[WorkspaceSnapshot]:
        """Build the graph for `now`'s local date and fetch unread messages; a failed fetch only degrades.

        Fails with the graph build's category (`Validation` for an unknown timezone, `Unavailable` when the
        projects root cannot be read).
        """
        started = time.monotonic()
        settings = self._settings
        local_date = local_date_in(now, settings.timezone)
        if isinstance(local_date, Err):
            return local_date
        projects = MarkdownProjectPlanAdapter(settings.projects_root, _PROJECTS, self._logger)
        plans = MarkdownDailyPlanAdapter(settings.daily_plans_root, _PLANS, self._logger)
        project_read = await projects.fetch_projects()
        plan_read = await plans.fetch_plans(local_date.value)
        snapshot = project_read.value if project_read.ok else None
        daily_plans: tuple[DailyPlan, ...] = plan_read.value if plan_read.ok else ()
        graph = build_state_graph(
            [
                ProjectPlanSourceRead(
                    name=_PROJECTS, snapshot=snapshot, error=None if snapshot else project_read.message
                )
            ],
            [DailyPlanSourceRead(name=_PLANS, plans=daily_plans, error=None if plan_read.ok else plan_read.message)],
            StateGraphSettings(
                workspace_root=settings.workspace_root.as_posix(),
                projects_root=settings.projects_root.as_posix(),
                daily_plans_root=settings.daily_plans_root.as_posix(),
                user=settings.user,
                timezone=settings.timezone,
                file_hashes=_file_hashes(settings.projects_root),
            ),
            now,
        )
        if isinstance(graph, Err):
            self._logger.error("workspace not read", fields={"category": str(graph.category)}, operation=_OPERATION)
            return graph
        messages, cursors, sources = await self._fetch(now)
        existing = next((p for p in daily_plans if p.local_date == local_date.value), None)
        previous = next((p for p in daily_plans if p.local_date < local_date.value), None)
        malformed = (snapshot.malformed_records if snapshot is not None else ()) + plans.malformed_records
        fields: dict[str, object] = {
            "tasks": len(graph.value.records.tasks),
            "plans": len(daily_plans),
            "messages": len(messages),
            "malformed": len(malformed),
            "elapsed_ms": round((time.monotonic() - started) * 1000, 3),
        }
        self._logger.info("workspace read", fields=fields, operation=_OPERATION)
        return ok(
            WorkspaceSnapshot(
                graph=graph.value,
                blockers={b.id: b for b in snapshot.blockers} if snapshot is not None else {},
                existing_plan=existing,
                previous_plan=previous,
                messages=messages,
                cursors=cursors,
                sources=sources,
                malformed_files=malformed,
            )
        )

    async def _fetch(
        self, now: datetime
    ) -> tuple[tuple[Message, ...], FetchCursors | None, tuple[MessageSourceStatus, ...]]:
        if self._communication is None or self._cursor_store is None:
            return (), None, ()
        name = self._communication.name
        since = self._cursor_store.load()
        if not since.ok:
            status = MessageSourceStatus(name=name, status="error", since=now, fetched=0, error=since.message)
            return (), None, (status,)
        batch = await self._communication.fetch_new_messages(since.value)
        if not batch.ok:
            self._logger.warn("messages not fetched", fields={"source": name}, operation=_OPERATION)
            status = MessageSourceStatus(name=name, status="error", since=now, fetched=0, error=batch.message)
            return (), None, (status,)
        fetched = batch.value
        status = MessageSourceStatus(name=name, status="ok", since=now, fetched=len(fetched.messages), error=None)
        return fetched.messages, fetched.cursors, (status,)
