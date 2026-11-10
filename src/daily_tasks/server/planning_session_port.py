"""Responsibility: Define the behavioral port for MCP planning session operations across single and dynamic workspaces.
Public interface:
`-- PlanningSessionPort
    +-- advance_screen(session_id, target_screen)
    +-- cancel_session(session_id)
    +-- confirm_plan(session_id, confirmed)
    +-- execute_operations(session_id, original_words, operations, verdicts)
    +-- get_fetch_window(sources, workspace_root)
    +-- get_session_state(session_id)
    `-- start_session(date, focus, messages, checked_sources, workspace_root)

Structural port satisfied by `PlanningTools` and `PlanningToolsDispatcher`.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Protocol

from pydantic import JsonValue

from daily_tasks.server.planning_tools import ToolBody


class PlanningSessionPort(Protocol):
    """Port exposing deterministic planning session tools to `McpServer`."""

    async def start_session(
        self,
        date: str | None = None,
        focus: str | None = None,
        messages: Sequence[Mapping[str, JsonValue]] = (),
        checked_sources: Sequence[str] = (),
        workspace_root: str | None = None,
    ) -> ToolBody:
        """Start today's planning session and return Screen 1."""
        ...

    def get_fetch_window(
        self,
        sources: Sequence[str] = ("gmail", "slack"),
        workspace_root: str | None = None,
    ) -> ToolBody:
        """Return saved fetch cursors or initial lookback windows for `sources`."""
        ...

    def get_session_state(self, session_id: str) -> ToolBody:
        """Return the current screen of an active planning session."""
        ...

    def execute_operations(
        self,
        session_id: str,
        original_words: str,
        operations: Sequence[Mapping[str, JsonValue]] = (),
        verdicts: Sequence[Mapping[str, JsonValue]] = (),
    ) -> ToolBody:
        """Stage explicit verdicts and operations against an active session."""
        ...

    def advance_screen(self, session_id: str, target_screen: int) -> ToolBody:
        """Advance an active session to `target_screen` (2 or 3)."""
        ...

    def confirm_plan(self, session_id: str, confirmed: bool) -> ToolBody:
        """Persist staged changes and today's daily plan when `confirmed` is True."""
        ...

    def cancel_session(self, session_id: str) -> ToolBody:
        """Discard an active session without writing any workspace files."""
        ...
