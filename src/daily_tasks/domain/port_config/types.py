# Responsibility: Group the port configuration profile extension DTOs.
# Public interface:
# +-- CommunicationBinding
# |   +-- adapter
# |   +-- channels
# |   +-- credentials_file
# |   +-- download_attachments
# |   +-- enabled
# |   +-- fetch_limit
# |   +-- max_attachment_bytes
# |   +-- name
# |   +-- package
# |   +-- poll_interval_seconds
# |   +-- read_only
# |   +-- scopes
# |   `-- token_env_var
# +-- FileStoreBinding
# |   +-- adapter
# |   +-- daily_plans_root
# |   +-- name
# |   +-- records_root
# |   +-- settings
# |   `-- state_root
# +-- PortConfig
# |   +-- credentials_root
# |   +-- description
# |   +-- messages_root
# |   +-- ports
# |   +-- schema
# |   +-- title
# |   +-- type
# |   `-- workspace_root
# +-- Ports
# |   +-- communication
# |   +-- daily_plan
# |   +-- file_store
# |   `-- project_plan
# `-- SourceBinding
#     +-- adapter
#     +-- enabled
#     +-- name
#     +-- path
#     `-- settings
"""PortConfig: roots and adapter bindings for each pluggable port."""

from collections.abc import Mapping

from pydantic import MISSING, Field, JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SourceBinding:
    """Project-plan or daily-plan source bound to an adapter."""

    name: str
    adapter: str
    enabled: bool
    path: str
    settings: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class CommunicationBinding:
    """Read-only communication source bound to an adapter."""

    name: str
    adapter: str
    enabled: bool
    package: str
    read_only: bool
    scopes: tuple[str, ...]
    credentials_file: str | MISSING = MISSING
    token_env_var: str | MISSING = MISSING
    channels: tuple[str, ...] | MISSING = MISSING
    fetch_limit: int
    poll_interval_seconds: int
    download_attachments: bool | MISSING = MISSING
    max_attachment_bytes: int | MISSING = MISSING


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FileStoreBinding:
    """File store adapter and the roots it writes under."""

    name: str
    adapter: str
    records_root: str
    daily_plans_root: str
    state_root: str
    settings: Mapping[str, JsonValue]


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Ports:
    """Adapter bindings per port."""

    project_plan: tuple[SourceBinding, ...]
    daily_plan: tuple[SourceBinding, ...]
    communication: tuple[CommunicationBinding, ...]
    file_store: FileStoreBinding


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PortConfig:
    """Profile extension configuring the server's roots and ports."""

    schema: str | MISSING = Field(default=MISSING, alias="$schema")
    title: str | MISSING = MISSING
    description: str | MISSING = MISSING
    type: str | MISSING = MISSING
    workspace_root: str
    messages_root: str
    credentials_root: str
    ports: Ports
