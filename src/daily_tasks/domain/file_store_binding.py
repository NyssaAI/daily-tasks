# Responsibility: Represent an immutable FileStoreBinding DTO.
# Public interface:
# `-- FileStoreBinding
#     +-- adapter
#     +-- daily_plans_root
#     +-- name
#     +-- records_root
#     +-- settings
#     `-- state_root
"""FileStoreBinding DTO."""

from collections.abc import Mapping

from pydantic import JsonValue
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FileStoreBinding:
    """File store adapter and the roots it writes under."""

    name: str
    adapter: str
    records_root: str
    daily_plans_root: str
    state_root: str
    settings: Mapping[str, JsonValue]
