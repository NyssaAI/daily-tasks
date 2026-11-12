"""Responsibility: Represent immutable per-source fetch cursors for a vault.
Public interface:
`-- FetchCursors
    +-- cursors
    `-- vault_root
"""

from collections.abc import Mapping

from pydantic.dataclasses import dataclass

from daily_tasks.core.communications.fetch_cursor import FetchCursor
from daily_tasks.core.records.dto_config import DTO_CONFIG


@dataclass(frozen=True, slots=True, kw_only=True, config=DTO_CONFIG)
class FetchCursors:
    """Fetch cursors per communication source (`<runtime_root>/fetch-cursors.json`)."""

    vault_root: str
    cursors: Mapping[str, FetchCursor]
