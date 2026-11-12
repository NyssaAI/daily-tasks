"""Responsibility: Define the role-named CollaboratorResolver contract for dynamic vault routing.
Public interface:
`-- CollaboratorResolver
    `-- resolve(vault_root)
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.planning.session_collaborators import SessionCollaborators


class CollaboratorResolver(Protocol):
    """Resolve per-vault `SessionCollaborators` for an optional `vault_root` override."""

    def resolve(self, vault_root: str | None) -> Result[SessionCollaborators]:
        """Return the wired collaborators for `vault_root` (or the configured default vault)."""
        ...
