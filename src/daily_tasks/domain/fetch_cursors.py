# Responsibility: Represent an immutable FetchCursors DTO.
# Public interface:
# `-- FetchCursors
#     +-- cursors
#     `-- workspace_root
"""FetchCursors DTO."""

from collections.abc import Mapping

from pydantic.dataclasses import dataclass

from daily_tasks.domain.dto_config import DTO_CONFIG
from daily_tasks.domain.fetch_cursor import FetchCursor


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FetchCursors:
    """Fetch cursors per source (`.nyssa-ai/daily-tasks/fetch-cursors.json`)."""

    workspace_root: str
    cursors: Mapping[str, FetchCursor]
