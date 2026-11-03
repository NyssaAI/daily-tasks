# Responsibility: Expose deterministic message pre-matching, signal detection and draft suggestion generation.
# Public interface:
# (none)
"""Deterministic pre-matching of fetched messages to tasks and blockers; zero LLM calls, no I/O."""

from daily_tasks.matching.build_message_graph import build_message_graph
from daily_tasks.matching.detect_signals import SIGNAL_PHRASES, detect_signals
from daily_tasks.matching.generate_suggestions import MIN_LINK_CONFIDENCE, generate_suggestions
from daily_tasks.matching.match_messages import LINK_CONFIDENCE, match_messages
from daily_tasks.matching.normalize_text import normalize_text
from daily_tasks.matching.types import MatchedLink, MessageMatch, Signal, SignalKind

__all__ = [
    "MIN_LINK_CONFIDENCE",
    "LINK_CONFIDENCE",
    "SIGNAL_PHRASES",
    "MatchedLink",
    "MessageMatch",
    "Signal",
    "SignalKind",
    "build_message_graph",
    "detect_signals",
    "generate_suggestions",
    "match_messages",
    "normalize_text",
]
