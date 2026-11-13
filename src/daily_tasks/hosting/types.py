"""Responsibility: Define immutable configuration value objects for hosting the Daily Tasks server.
Public interface:
+-- ServerOverrides
|   +-- config_dir
|   +-- daily_plans_root
|   +-- initial_lookback_days
|   +-- projects_root
|   +-- repo_root
|   +-- runtime_root
|   +-- telemetry_enabled
|   +-- timezone
|   +-- user_email
|   +-- user_name
|   `-- vault_root
`-- ServerSettings
    +-- config_dir
    +-- daily_plans_root
    +-- initial_lookback_days
    +-- projects_root
    +-- runtime_root
    +-- telemetry_enabled
    +-- timezone
    +-- user
    `-- vault_root
"""

from dataclasses import dataclass
from pathlib import Path

from daily_tasks.core.records.graph_user import GraphUser


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerOverrides:
    """Explicit CLI/environment overrides layered over `user_home` and `repo_root` `config.json` files."""

    vault_root: Path | None = None
    projects_root: str | None = None
    daily_plans_root: str | None = None
    runtime_root: Path | None = None
    repo_root: Path | None = None
    user_email: str | None = None
    user_name: str | None = None
    timezone: str | None = None
    initial_lookback_days: int | None = None
    config_dir: Path | None = None
    telemetry_enabled: bool | None = None


@dataclass(frozen=True, slots=True, kw_only=True)
class ServerSettings:
    """Validated settings for reading a vault and persisting operational state in `runtime_root`."""

    vault_root: Path
    projects_root: Path
    daily_plans_root: Path
    runtime_root: Path
    user: GraphUser
    timezone: str
    initial_lookback_days: int = 7
    config_dir: Path | None = None
    telemetry_enabled: bool = False
