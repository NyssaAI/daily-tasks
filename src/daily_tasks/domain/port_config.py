# Responsibility: Represent an immutable PortConfig DTO.
# Public interface:
# `-- PortConfig
#     +-- credentials_root
#     +-- description
#     +-- messages_root
#     +-- ports
#     +-- schema
#     +-- title
#     +-- type
#     `-- workspace_root
"""PortConfig DTO."""

from pydantic import Field, MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.ports import Ports


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

