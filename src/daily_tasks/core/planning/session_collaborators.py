"""Responsibility: Bundle the collaborators needed to run planning tools for one vault.
Public interface:
`-- SessionCollaborators
    +-- committer
    +-- context
    +-- cursor_store
    `-- reader
"""

from dataclasses import dataclass

from daily_tasks.core.communications.cursor_store import CursorStore
from daily_tasks.core.planning.session_committer import SessionCommitter
from daily_tasks.core.planning.types import PlanningContext
from daily_tasks.core.planning.vault_reader import VaultReader


@dataclass(frozen=True, slots=True, kw_only=True)
class SessionCollaborators:
    """Resolved context, reader, committer, and optional cursor store for one vault."""

    context: PlanningContext
    reader: VaultReader
    committer: SessionCommitter
    cursor_store: CursorStore | None = None
