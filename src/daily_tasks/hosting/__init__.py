"""Hosting composition root, 5-root settings resolution (`vault_root` & `runtime_root`), and setup tools."""

from daily_tasks.hosting.compose_mcp_server import compose_mcp_server
from daily_tasks.hosting.detect_host_timezone import detect_host_timezone, valid_iana_timezone
from daily_tasks.hosting.inspect_setup_status import build_sources_config, inspect_setup_status
from daily_tasks.hosting.new_uuid7 import new_uuid7
from daily_tasks.hosting.profile_store import ProfileStore
from daily_tasks.hosting.resolve_runtime_root import (
    RUNTIME_ROOT_ENV_VAR,
    is_agent_runtime_root,
    resolve_runtime_root,
)
from daily_tasks.hosting.resolve_server_settings import (
    DEFAULT_DAILY_PLANS_RELATIVE,
    DEFAULT_PROJECTS_ROOT,
    resolve_default_vault_root,
    resolve_server_settings,
)
from daily_tasks.hosting.secret_tools import SecretTools
from daily_tasks.hosting.setup_tools import SetupTools
from daily_tasks.hosting.types import ServerOverrides, ServerSettings
from daily_tasks.hosting.vault_collaborator_resolver import VaultCollaboratorResolver
from daily_tasks.hosting.vault_reader_markdown import VaultReaderMarkdown

__all__ = [
    "DEFAULT_DAILY_PLANS_RELATIVE",
    "DEFAULT_PROJECTS_ROOT",
    "ProfileStore",
    "RUNTIME_ROOT_ENV_VAR",
    "SecretTools",
    "ServerOverrides",
    "ServerSettings",
    "SetupTools",
    "VaultCollaboratorResolver",
    "VaultReaderMarkdown",
    "build_sources_config",
    "compose_mcp_server",
    "detect_host_timezone",
    "inspect_setup_status",
    "is_agent_runtime_root",
    "new_uuid7",
    "resolve_default_vault_root",
    "resolve_runtime_root",
    "resolve_server_settings",
    "valid_iana_timezone",
]
