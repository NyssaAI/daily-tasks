"""Responsibility: Represent an immutable CommunicationBinding DTO.
Public interface:
`-- CommunicationBinding
    +-- adapter
    +-- channels
    +-- credentials_file
    +-- download_attachments
    +-- enabled
    +-- fetch_limit
    +-- max_attachment_bytes
    +-- name
    +-- package
    +-- poll_interval_seconds
    +-- read_only
    +-- scopes
    `-- token_env_var

CommunicationBinding DTO.
"""

from pydantic import MISSING, Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class CommunicationBinding:
    """Read-only communication source bound to an adapter; `credentials_file` is deprecated."""

    name: str
    adapter: str
    enabled: bool
    package: str
    read_only: bool
    scopes: tuple[str, ...]
    credentials_file: str | MISSING = Field(
        default=MISSING,
        deprecated="Use token_env_var or a keyring-sealed configuration entry resolved by SecretResolver.",
    )
    token_env_var: str | MISSING = MISSING
    channels: tuple[str, ...] | MISSING = MISSING
    fetch_limit: int
    poll_interval_seconds: int
    download_attachments: bool | MISSING = MISSING
    max_attachment_bytes: int | MISSING = MISSING
