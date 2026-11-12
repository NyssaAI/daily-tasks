"""Responsibility: Define the repository contract for reading and persisting pending suggestions.
Public interface:
`-- SuggestionsRepository
    +-- load()
    `-- save(suggestions)
"""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.core.communications.suggestions import Suggestions


class SuggestionsRepository(Protocol):
    """Repository managing pending communication-derived suggestions in `runtime_root`."""

    def load(self) -> Result[Suggestions]:
        """Load pending suggestions, or return an empty buffer when none have been saved yet."""
        ...

    def save(self, suggestions: Suggestions) -> Result[None]:
        """Atomically persist the updated pending suggestions buffer."""
        ...
