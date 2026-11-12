"""Responsibility: Define the role-named SetupHandler contract for MCP setup tools.
Public interface:
`-- SetupHandler
    +-- configure_vault(spec)
    `-- setup_status(vault_root)
"""

from typing import Protocol

from pydantic import JsonValue

from daily_tasks.transports.mcp.types import VaultSetupSpec


class SetupHandler(Protocol):
    """Inspect setup gates and persist user-confirmed Schema Version 2 Daily Tasks configuration."""

    def setup_status(self, vault_root: str | None = None) -> dict[str, JsonValue]:
        """Inspect setup status for `vault_root` read-only."""
        ...

    def configure_vault(self, spec: VaultSetupSpec) -> dict[str, JsonValue]:
        """Persist validated Schema Version 2 configuration and seed vault templates when `spec.confirmed` is true."""
        ...
