"""Responsibility: Represent an immutable Today DTO.
Public interface:
`-- Today
    +-- available
    +-- future
    `-- selected

Today DTO.
"""

from collections.abc import Mapping
from datetime import date

from pydantic import UUID7
from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.today_selection import TodaySelection


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Today:
    """Today's selection, available items and items planned for later days."""

    selected: TodaySelection
    available: tuple[UUID7, ...]
    future: Mapping[date, tuple[UUID7, ...]]
