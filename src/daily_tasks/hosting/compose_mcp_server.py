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
from daily_tasks.hosting.profile_store import ProfileStore
from daily_tasks.hosting.record_usage_event import extract_telemetry_enabled, record_usage_event
from daily_tasks.hosting.resolve_runtime_root import resolve_runtime_root
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


def _tool_usage_hook(
    overrides: ServerOverrides,
    store: ProfileStore,
    clock: Callable[[], datetime],
    environ: Mapping[str, str] | None,
    cwd: Path | None,
) -> Callable[[str, str, float], None]:
    def record_call(tool: str, status: str, elapsed_ms: float) -> None:
        layered = store.read_layered()
        layered_doc = layered.value if layered.ok else {}
        enabled = overrides.telemetry_enabled
        if enabled is None:
            extracted = extract_telemetry_enabled(layered_doc)
            enabled = extracted.value if extracted.ok else False
        if not enabled:
            return
        raw_rt = layered_doc.get("runtimeRoot")
        configured_rt = raw_rt.strip() if isinstance(raw_rt, str) and raw_rt.strip() else None
        rt_res = resolve_runtime_root(
            explicit=overrides.runtime_root,
            environ=environ,
            cwd=cwd,
            configured=configured_rt,
            config_dir=store.user_dir,
            repo_root=overrides.repo_root,
        )
        if not rt_res.ok:
            return
        record_usage_event(
            rt_res.value,
            {
                "elapsed_ms": elapsed_ms,
                "event": "mcp.tool_call",
                "status": status,
                "timestamp": clock().isoformat().replace("+00:00", "Z"),
                "tool": tool,
            },
            enabled=True,
        )

    return record_call


def compose_mcp_server(
    overrides: ServerOverrides,
    version: str,
    clock: Callable[[], datetime],
    new_id: Callable[[], UUID],
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
) -> McpServer:
    """Wire `VaultCollaboratorResolver`, `PlanningToolsDispatcher`, `SecretTools`, `SetupTools`, and `McpServer`."""
    store = ProfileStore(config_dir=overrides.config_dir, repo_root=overrides.repo_root)
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
    on_tool_call = _tool_usage_hook(overrides, store, clock, environ, cwd)
    return McpServer(dispatcher, version, _secret_tools(store.user_dir), setup_tools, on_tool_call=on_tool_call)
