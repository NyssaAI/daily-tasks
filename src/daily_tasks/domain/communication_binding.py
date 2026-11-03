# Responsibility: Represent an immutable CommunicationBinding DTO.
# Public interface:
# `-- CommunicationBinding
#     +-- adapter
#     +-- channels
#     +-- credentials_file
#     +-- download_attachments
#     +-- enabled
#     +-- fetch_limit
#     +-- max_attachment_bytes
#     +-- name
#     +-- package
#     +-- poll_interval_seconds
#     +-- read_only
#     +-- scopes
#     `-- token_env_var
"""CommunicationBinding DTO."""

from pydantic import MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG


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

