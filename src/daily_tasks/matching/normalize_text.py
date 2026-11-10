"""Responsibility: Normalize free text for deterministic title comparison.
Public interface:
`-- normalize_text(text)

Casefold, replace punctuation with spaces and collapse whitespace.
"""

import re
from typing import Final

_PUNCTUATION: Final[re.Pattern[str]] = re.compile(r"[^\w\s]|_")


def normalize_text(text: str) -> str:
    """Return `text` casefolded, punctuation-stripped and whitespace-collapsed."""
    return " ".join(_PUNCTUATION.sub(" ", text.casefold()).split())
