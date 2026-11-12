"""Responsibility: Define the discriminator for communication-derived update suggestions.
Public interface:
`-- SuggestionKind
"""

from typing import Literal

type SuggestionKind = Literal["new-task", "status", "dod", "blocker"]
