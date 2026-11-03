# Responsibility: Represent an immutable Screen DTO.
# Public interface:
# `-- Screen
#     +-- kind
#     +-- numbering
#     +-- rows
#     `-- shown_at
"""Screen DTO."""

from collections.abc import Mapping
from typing import Literal
from pydantic import MISSING
from pydantic.dataclasses import dataclass
from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.utc_timestamp import UtcTimestamp
from daily_tasks.domain.row_ref import RowRef


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class Screen:
    """Screen shown in the session and how its rows are numbered."""

    kind: Literal["plan-the-day", "assign-days", "confirm"]
    numbering: Literal["session", "screen"]
    shown_at: UtcTimestamp | None
    rows: Mapping[int, RowRef] | MISSING = MISSING

