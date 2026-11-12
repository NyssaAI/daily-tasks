"""Responsibility: Represent an immutable PortConfig record.
Public interface:
`-- PortConfig
    +-- credentials_root
    +-- description
    +-- messages_root
    +-- ports
    +-- schema
    +-- title
    +-- type
    `-- vault_root
"""

from pydantic import MISSING, Field
from pydantic.dataclasses import dataclass

from daily_tasks.core.planning.ports import Ports
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class PortConfig:
    """Profile extension configuring the server's roots and collaborator bindings."""

    schema: str | MISSING = Field(default=MISSING, alias="$schema")
    title: str | MISSING = MISSING
    description: str | MISSING = MISSING
    type: str | MISSING = MISSING
    vault_root: str
    messages_root: str
    credentials_root: str | MISSING = Field(
        default=MISSING,
        deprecated="Credentials are resolved into memory by SecretResolver; no credentials directory is read.",
    )
    ports: Ports
