"""Responsibility: Expose the MCP stdio server that drives the deterministic planning session.
Public interface:
(none)

MCP server: JSON-RPC protocol handling, the planning and secret tools and the stdio transport.
"""

from daily_tasks.server.markdown_workspace_reader import MarkdownWorkspaceReader
from daily_tasks.server.mcp_server import McpServer
from daily_tasks.server.planning_session_port import PlanningSessionPort
from daily_tasks.server.planning_tools import PlanningTools
from daily_tasks.server.planning_tools_dispatcher import PlanningToolsDispatcher
from daily_tasks.server.resolve_server_settings import read_layered_profile, resolve_server_settings
from daily_tasks.server.secret_tools import SecretTools
from daily_tasks.server.serve_stdio import serve_stdio
from daily_tasks.server.types import ServerOverrides, ServerSettings, WorkspaceSnapshot
from daily_tasks.server.workspace_reader import WorkspaceReader

__all__ = [
    "MarkdownWorkspaceReader",
    "McpServer",
    "PlanningSessionPort",
    "PlanningTools",
    "PlanningToolsDispatcher",
    "SecretTools",
    "ServerOverrides",
    "ServerSettings",
    "WorkspaceReader",
    "WorkspaceSnapshot",
    "read_layered_profile",
    "resolve_server_settings",
    "serve_stdio",
]
