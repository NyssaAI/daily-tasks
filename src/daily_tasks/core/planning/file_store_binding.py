"""Responsibility: Represent an immutable FileStoreBinding record.
Public interface:
`-- FileStoreBinding
    +-- adapter
    +-- daily_plans_root
    +-- name
    +-- records_root
    +-- runtime_root
    `-- settings
"""

from collections.abc import Mapping

from pydantic import JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FileStoreBinding:
    """File store implementation and the roots it writes under."""

    name: str
    adapter: str
    records_root: str
    daily_plans_root: str
    runtime_root: str
    settings: Mapping[str, JsonValue]
