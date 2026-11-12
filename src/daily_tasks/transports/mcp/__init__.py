"""Thin MCP JSON-RPC stdio transport adapter."""

from daily_tasks.transports.mcp.mcp_server import McpServer
from daily_tasks.transports.mcp.secret_capturer import SecretCapturer
from daily_tasks.transports.mcp.serve_stdio import serve_stdio
from daily_tasks.transports.mcp.setup_handler import SetupHandler
from daily_tasks.transports.mcp.tool_definitions import (
    CONFIGURE_VAULT_TOOL,
    SECRET_TOOL,
    SECRET_TOOL_DEFINITIONS,
    SETUP_STATUS_TOOL,
    SETUP_TOOL_DEFINITIONS,
    TOOL_DEFINITIONS,
)
from daily_tasks.transports.mcp.types import VaultSetupSpec

__all__ = [
    "CONFIGURE_VAULT_TOOL",
    "McpServer",
    "SECRET_TOOL",
    "SECRET_TOOL_DEFINITIONS",
    "SETUP_STATUS_TOOL",
    "SETUP_TOOL_DEFINITIONS",
    "SecretCapturer",
    "SetupHandler",
    "TOOL_DEFINITIONS",
    "VaultSetupSpec",
    "serve_stdio",
]
