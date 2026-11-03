# Responsibility: Detect status signal phrases in message text.
# Public interface:
# +-- SIGNAL_PHRASES
# `-- detect_signals(text)
"""Word-boundary, casefolded signal phrase detection with a simple `not` negation guard."""

import re
from collections.abc import Mapping
from types import MappingProxyType
from typing import Final

from daily_tasks.matching.types import Signal, SignalKind

SIGNAL_PHRASES: Final[Mapping[str, SignalKind]] = MappingProxyType(
    {
        "done": "completion",
        "completed": "completion",
        "merged": "completion",
        "resolved": "completion",
        "unblocked": "completion",
        "blocked": "blocked",
        "stuck": "blocked",
        "waiting on": "blocked",
        "can you": "request",
    }
)

_QUOTE_LIMIT: Final[int] = 160
_PATTERN: Final[re.Pattern[str]] = re.compile(
    r"(?<![\w-])(?<!\bnot )(?<!n't )("
    + "|".join(re.escape(phrase).replace(r"\ ", r"\s+") for phrase in SIGNAL_PHRASES)
    + r")(?![\w-])",
    re.IGNORECASE,
)
_SENTENCE_END: Final[re.Pattern[str]] = re.compile(r"[.!?\n]")


def _quote(text: str, start: int, end: int) -> str:
    before = [m.end() for m in _SENTENCE_END.finditer(text, 0, start)]
    after = _SENTENCE_END.search(text, end)
    sentence = " ".join(text[before[-1] if before else 0 : after.start() if after else len(text)].split())
    return sentence if len(sentence) <= _QUOTE_LIMIT else sentence[: _QUOTE_LIMIT - 3].rstrip() + "..."


def detect_signals(text: str) -> tuple[Signal, ...]:
    """Return each signal phrase occurrence in text order, once per (kind, phrase).

    Phrases match on word boundaries regardless of case; a phrase directly preceded by
    `not` or an `n't` contraction is ignored.
    """
    signals: list[Signal] = []
    seen: set[str] = set()
    for found in _PATTERN.finditer(text):
        phrase = " ".join(found.group(1).casefold().split())
        if phrase in seen:
            continue
        seen.add(phrase)
        quote = _quote(text, found.start(), found.end())
        signals.append(Signal(kind=SIGNAL_PHRASES[phrase], phrase=phrase, quote=quote))
    return tuple(signals)
