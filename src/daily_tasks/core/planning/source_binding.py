"""Responsibility: Represent an immutable SourceBinding DTO.
Public interface:
`-- SourceBinding
    +-- adapter
    +-- enabled
    +-- name
    +-- path
    `-- settings

SourceBinding DTO.
"""

from collections.abc import Mapping

from pydantic import JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class SourceBinding:
    """Project-plan or daily-plan source bound to an adapter."""

    name: str
    adapter: str
    enabled: bool
    path: str
    settings: Mapping[str, JsonValue]
