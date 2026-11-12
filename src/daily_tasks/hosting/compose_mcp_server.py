"""Responsibility: Compose the MCP server from core, feature slices, and hosting settings.
Public interface:
`-- compose_mcp_server(overrides, version, clock, new_id, environ, cwd)
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Final
from uuid import UUID

from nyssa_ai_configuration import BootstrapOptions
from nyssa_ai_result import Result

from daily_tasks.communications.secret_capture_service import SecretCaptureService
from daily_tasks.core.planning.planning_tools_dispatcher import PlanningToolsDispatcher
from daily_tasks.hosting.secret_tools import SecretTools
from daily_tasks.hosting.setup_tools import SetupTools
from daily_tasks.hosting.types import ServerOverrides
from daily_tasks.hosting.vault_collaborator_resolver import VaultCollaboratorResolver
from daily_tasks.transports.mcp.mcp_server import McpServer

_APPLICATION_NAME: Final = "daily-tasks"


def _secret_tools(config_dir: Path) -> SecretTools:
    options = BootstrapOptions(application_name=_APPLICATION_NAME, configuration_directory=str(config_dir))

    def open_service() -> Result[SecretCaptureService]:
        return SecretCaptureService.create(options)

    return SecretTools(open_service)


def compose_mcp_server(
    overrides: ServerOverrides,
    version: str,
    clock: Callable[[], datetime],
    new_id: Callable[[], UUID],
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> McpServer:
    """Wire `VaultCollaboratorResolver`, `PlanningToolsDispatcher`, `SecretTools`, `SetupTools`, and `McpServer`."""
    resolved_config_dir = (
        overrides.config_dir.expanduser().resolve()
        if overrides.config_dir is not None
        else (Path.home() / ".nyssa-ai" / _APPLICATION_NAME).resolve()
    )
    resolver = VaultCollaboratorResolver(
        overrides=overrides,
        clock=clock,
        environ=environ,
        cwd=cwd,
    )
    dispatcher = PlanningToolsDispatcher(
        resolver=resolver,
        clock=clock,
        new_id=new_id,
    )
    setup_tools = SetupTools(overrides=overrides, clock=clock, plugin_version=version)
    return McpServer(dispatcher, version, _secret_tools(resolved_config_dir), setup_tools)
