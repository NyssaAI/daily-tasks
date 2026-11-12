"""Responsibility: Define immutable request records for MCP transport tool handlers.
Public interface:
`-- VaultSetupSpec
    +-- confirmed
    +-- daily_plans_relative
    +-- disabled_sources
    +-- harness_connections
    +-- initial_lookback_days
    +-- priorities
    +-- projects_root
    +-- scope
    +-- set_default_vault
    +-- standalone_sources
    +-- templates_dir
    +-- timezone
    +-- user_email
    +-- user_name
    `-- vault_root
"""

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from pydantic import JsonValue


@dataclass(frozen=True, slots=True, kw_only=True)
class VaultSetupSpec:
    """Validated arguments for `daily_tasks_configure_vault`."""

    confirmed: bool
    scope: str = "vault"
    vault_root: str | None = None
    user_name: str | None = None
    user_email: str | None = None
    timezone: str | None = None
    priorities: Sequence[str] | None = None
    projects_root: str | None = None
    daily_plans_relative: str | None = None
    templates_dir: str | None = None
    harness_connections: Sequence[Mapping[str, JsonValue]] | None = None
    standalone_sources: Sequence[str] | None = None
    disabled_sources: Sequence[str] | None = None
    initial_lookback_days: int = 7
    set_default_vault: bool = True
