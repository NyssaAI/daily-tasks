"""Responsibility: Read configured record repositories concurrently and build the state graph.
Public interface:
`-- StateGraphBuilder
    +-- build()
    `-- new(project_repositories, plan_repositories, settings, clock)
"""

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Final, final

from nyssa_ai_result import Err, Result

from daily_tasks.core.records.build_state_graph import build_state_graph
from daily_tasks.core.records.daily_plan_repository import DailyPlanRepository
from daily_tasks.core.records.local_date_in import local_date_in
from daily_tasks.core.records.project_plan_repository import ProjectPlanRepository
from daily_tasks.core.records.state_graph import StateGraph
from daily_tasks.core.records.types import DailyPlanRead, ProjectPlanRead, StateGraphSettings

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "state_graph.build"


@final
class StateGraphBuilder:
    """Build a fresh state graph from configured project-plan and daily-plan repositories."""

    def __init__(
        self,
        project_repositories: Sequence[ProjectPlanRepository],
        plan_repositories: Sequence[DailyPlanRepository],
        settings: StateGraphSettings,
        clock: Callable[[], datetime],
    ) -> None:
        """Borrow the repositories; `clock` returns the current UTC time."""
        self._project_repositories = tuple(project_repositories)
        self._plan_repositories = tuple(plan_repositories)
        self._settings = settings
        self._clock = clock

    async def build(self) -> Result[StateGraph]:
        """Read all repositories concurrently and compile the state graph."""
        started = time.monotonic()
        built_at = self._clock()
        local_date = local_date_in(built_at, self._settings.timezone)
        if isinstance(local_date, Err):
            self._log_failure(local_date, started)
            return local_date
        project_results, plan_results = await asyncio.gather(
            asyncio.gather(*(repo.fetch_projects() for repo in self._project_repositories)),
            asyncio.gather(*(repo.fetch_plans(local_date.value) for repo in self._plan_repositories)),
        )
        project_reads = [
            ProjectPlanRead(name=repo.name, snapshot=None, error=result.message)
            if isinstance(result, Err)
            else ProjectPlanRead(name=repo.name, snapshot=result.value)
            for repo, result in zip(self._project_repositories, project_results, strict=True)
        ]
        plan_reads = [
            DailyPlanRead(name=repo.name, plans=(), error=result.message)
            if isinstance(result, Err)
            else DailyPlanRead(name=repo.name, plans=result.value)
            for repo, result in zip(self._plan_repositories, plan_results, strict=True)
        ]
        graph = build_state_graph(project_reads, plan_reads, self._settings, built_at)
        if isinstance(graph, Err):
            self._log_failure(graph, started)
            return graph
        self._log_success(graph.value, started)
        return graph

    def _log_success(self, graph: StateGraph, started: float) -> None:
        failed = [source.name for source in graph.context.sources if source.status != "ok"]
        fields: dict[str, object] = {
            "local_date": graph.context.local_date.isoformat(),
            "projects": len(graph.records.projects),
            "tasks": len(graph.records.tasks),
            "plans": len(graph.records.plans),
            "diagnostics": len(graph.diagnostics),
            "failed_sources": failed,
            "elapsed_ms": _elapsed_ms(started),
        }
        if failed:
            _LOGGER.warning(
                "state graph built with unavailable sources",
                extra={"operation": _OPERATION, "fields": fields},
            )
        else:
            _LOGGER.info("state graph built", extra={"operation": _OPERATION, "fields": fields})

    def _log_failure(self, failure: Err[object], started: float) -> None:
        fields = {"category": str(failure.category), "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.error("state graph not built", extra={"operation": _OPERATION, "fields": fields})


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
