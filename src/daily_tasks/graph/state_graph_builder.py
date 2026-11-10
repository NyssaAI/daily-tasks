"""Responsibility: Read every configured record source concurrently and build the state graph.
Public interface:
`-- StateGraphBuilder
    +-- build()
    `-- new(project_ports, plan_ports, settings, clock)

Imperative shell of `collect_current_state`: await the read ports, then call `build_state_graph`.
"""

import asyncio
import logging
import time
from collections.abc import Callable, Sequence
from datetime import datetime
from typing import Final, final

from nyssa_ai_result import Err, Result

from daily_tasks.domain import StateGraph
from daily_tasks.graph.build_state_graph import build_state_graph
from daily_tasks.graph.local_date_in import local_date_in
from daily_tasks.graph.types import DailyPlanSourceRead, ProjectPlanSourceRead, StateGraphSettings
from daily_tasks.ports import DailyPlanPort, ProjectPlanPort

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "state_graph.build"


@final
class StateGraphBuilder:
    """Build a fresh state graph from all configured project-plan and daily-plan ports."""

    def __init__(
        self,
        project_ports: Sequence[ProjectPlanPort],
        plan_ports: Sequence[DailyPlanPort],
        settings: StateGraphSettings,
        clock: Callable[[], datetime],
    ) -> None:
        """Borrow the ports; `clock` returns the current UTC time."""
        self._project_ports = tuple(project_ports)
        self._plan_ports = tuple(plan_ports)
        self._settings = settings
        self._clock = clock

    async def build(self) -> Result[StateGraph]:
        """Read all ports concurrently and build the graph; a failing source does not stop the others.

        Fails with `Validation` for a non-UTC clock or unknown timezone, and with `Unavailable` when no
        project-plan source could be read. Cancellation propagates.
        """
        started = time.monotonic()
        built_at = self._clock()
        local_date = local_date_in(built_at, self._settings.timezone)
        if isinstance(local_date, Err):
            self._log_failure(local_date, started)
            return local_date
        project_results, plan_results = await asyncio.gather(
            asyncio.gather(*(port.fetch_projects() for port in self._project_ports)),
            asyncio.gather(*(port.fetch_plans(local_date.value) for port in self._plan_ports)),
        )
        project_reads = [
            ProjectPlanSourceRead(name=port.name, snapshot=None, error=result.message)
            if isinstance(result, Err)
            else ProjectPlanSourceRead(name=port.name, snapshot=result.value)
            for port, result in zip(self._project_ports, project_results, strict=True)
        ]
        plan_reads = [
            DailyPlanSourceRead(name=port.name, plans=(), error=result.message)
            if isinstance(result, Err)
            else DailyPlanSourceRead(name=port.name, plans=result.value)
            for port, result in zip(self._plan_ports, plan_results, strict=True)
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
