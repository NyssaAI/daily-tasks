# Responsibility: Split a record title into normalized search terms.
# Public interface:
# `-- title_terms(title)
"""Lowercase word tokens of a title, without short words and common stop words."""

import re
from typing import Final

_WORD: Final[re.Pattern[str]] = re.compile(r"[a-z0-9]+")
_STOP_WORDS: Final[frozenset[str]] = frozenset(
    {"and", "the", "for", "with", "from", "into", "behind", "over", "after", "before", "via", "per", "our", "its"}
)


def title_terms(title: str) -> tuple[str, ...]:
    """Return distinct terms in first-seen order; terms have at least three characters."""
    terms: dict[str, None] = {}
    for word in _WORD.findall(title.lower()):
        if len(word) >= 3 and word not in _STOP_WORDS:
            terms[word] = None
    return tuple(terms)
