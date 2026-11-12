"""Responsibility: Read a Markdown vault and configured communication clients into one VaultSnapshot.
Public interface:
`-- VaultReaderMarkdown
    +-- new(settings, communication, cursor_store)
    `-- read(now)
"""

import hashlib
import logging
import time
from datetime import datetime
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import Err, Result, ok

from daily_tasks.core.communications.communication_client import CommunicationClient
from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.cursor_store import CursorStore
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.message_source_status import MessageSourceStatus
from daily_tasks.core.planning.types import VaultSnapshot
from daily_tasks.core.records.build_state_graph import build_state_graph
from daily_tasks.core.records.daily_plan import DailyPlan
from daily_tasks.core.records.local_date_in import local_date_in
from daily_tasks.core.records.types import DailyPlanRead, ProjectPlanRead, StateGraphSettings
from daily_tasks.hosting.types import ServerSettings
from daily_tasks.records.daily_plan_repository_markdown import DailyPlanRepositoryMarkdown
from daily_tasks.records.project_plan_repository_markdown import ProjectPlanRepositoryMarkdown

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "vault.read"
_PROJECTS: Final = "markdown-projects"
_PLANS: Final = "markdown-daily-plans"


def _file_hashes(root: Path) -> dict[str, str]:
    hashes: dict[str, str] = {}
    if not root.is_dir():
        return hashes
    for path in sorted(root.rglob("*.md")):
        try:
            hashes[path.relative_to(root).as_posix()] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        except OSError:
            continue
    return hashes


@final
class VaultReaderMarkdown:
    """Entity-first `VaultReader`: Markdown project/daily plan repositories, record hashes, and optional fetch."""

    def __init__(
        self,
        settings: ServerSettings,
        communication: CommunicationClient | None = None,
        cursor_store: CursorStore | None = None,
    ) -> None:
        """Keep the collaborators; nothing is read until `read`."""
        self._settings = settings
        self._communication = communication
        self._cursor_store = cursor_store

    async def read(self, now: datetime) -> Result[VaultSnapshot]:
        """Build the state graph for `now`'s local date and fetch unread communication messages."""
        started = time.monotonic()
        settings = self._settings
        local_date = local_date_in(now, settings.timezone)
        if isinstance(local_date, Err):
            return local_date
        projects = ProjectPlanRepositoryMarkdown(settings.projects_root, _PROJECTS)
        plans = DailyPlanRepositoryMarkdown(settings.daily_plans_root, _PLANS)
        project_read = await projects.fetch_projects()
        plan_read = await plans.fetch_plans(local_date.value)
        snapshot = project_read.value if project_read.ok else None
        daily_plans: tuple[DailyPlan, ...] = plan_read.value if plan_read.ok else ()
        graph = build_state_graph(
            [ProjectPlanRead(name=_PROJECTS, snapshot=snapshot, error=None if snapshot else project_read.message)],
            [DailyPlanRead(name=_PLANS, plans=daily_plans, error=None if plan_read.ok else plan_read.message)],
            StateGraphSettings(
                vault_root=settings.vault_root.as_posix(),
                projects_root=settings.projects_root.as_posix(),
                daily_plans_root=settings.daily_plans_root.as_posix(),
                user=settings.user,
                timezone=settings.timezone,
                file_hashes=_file_hashes(settings.projects_root),
            ),
            now,
        )
        if isinstance(graph, Err):
            _LOGGER.error(
                "vault not read",
                extra={"operation": _OPERATION, "fields": {"category": str(graph.category)}},
            )
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
        _LOGGER.info("vault read", extra={"operation": _OPERATION, "fields": fields})
        return ok(
            VaultSnapshot(
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
    ) -> tuple[tuple[CommunicationMessage, ...], FetchCursors | None, tuple[MessageSourceStatus, ...]]:
        if self._communication is None or self._cursor_store is None:
            return (), None, ()
        name = self._communication.name
        since = self._cursor_store.load()
        if not since.ok:
            status = MessageSourceStatus(name=name, status="error", since=now, fetched=0, error=since.message)
            return (), None, (status,)
        batch = await self._communication.fetch_new_messages(since.value)
        if not batch.ok:
            _LOGGER.warning("messages not fetched", extra={"operation": _OPERATION, "fields": {"source": name}})
            status = MessageSourceStatus(name=name, status="error", since=now, fetched=0, error=batch.message)
            return (), None, (status,)
        fetched = batch.value
        status = MessageSourceStatus(name=name, status="ok", since=now, fetched=len(fetched.messages), error=None)
        return fetched.messages, fetched.cursors, (status,)
