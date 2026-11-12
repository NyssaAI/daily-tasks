"""Core communication models, fetch-window/cursor contracts, and deterministic message correlation."""

from daily_tasks.core.communications.attachment import Attachment
from daily_tasks.core.communications.build_message_graph import build_message_graph
from daily_tasks.core.communications.communication_client import CommunicationClient
from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.compute_fetch_window import (
    DEFAULT_INITIAL_LOOKBACK_DAYS,
    compute_fetch_window,
)
from daily_tasks.core.communications.cursor_store import CursorStore
from daily_tasks.core.communications.detect_signals import detect_signals
from daily_tasks.core.communications.fetch_cursor import FetchCursor
from daily_tasks.core.communications.fetch_cursors import FetchCursors
from daily_tasks.core.communications.fetch_window import FetchWindow
from daily_tasks.core.communications.find_record_mentions import find_record_mentions
from daily_tasks.core.communications.for_review_message import ForReviewMessage
from daily_tasks.core.communications.generate_suggestions import MIN_LINK_CONFIDENCE, generate_suggestions
from daily_tasks.core.communications.ingest_harness_messages import ingest_harness_messages
from daily_tasks.core.communications.match_messages import LINK_CONFIDENCE, match_messages
from daily_tasks.core.communications.message_address import MessageAddress
from daily_tasks.core.communications.message_facts import MessageFacts
from daily_tasks.core.communications.message_graph import MessageGraph
from daily_tasks.core.communications.message_graph_context import MessageGraphContext
from daily_tasks.core.communications.message_graph_derived import MessageGraphDerived
from daily_tasks.core.communications.message_graph_index import MessageGraphIndex
from daily_tasks.core.communications.message_graph_record import MessageGraphRecord
from daily_tasks.core.communications.message_graph_summary import MessageGraphSummary
from daily_tasks.core.communications.message_link import MessageLink
from daily_tasks.core.communications.message_log import MessageLog
from daily_tasks.core.communications.message_log_entry import MessageLogEntry
from daily_tasks.core.communications.message_source_status import MessageSourceStatus
from daily_tasks.core.communications.message_source_tree import MessageSourceTree
from daily_tasks.core.communications.message_thread import MessageThread
from daily_tasks.core.communications.normalize_text import normalize_text
from daily_tasks.core.communications.suggestion import Suggestion
from daily_tasks.core.communications.suggestion_kind import SuggestionKind
from daily_tasks.core.communications.suggestion_target import SuggestionTarget
from daily_tasks.core.communications.suggestion_validation import SuggestionValidation
from daily_tasks.core.communications.suggestions import Suggestions
from daily_tasks.core.communications.suggestions_repository import SuggestionsRepository
from daily_tasks.core.communications.thread_facts import ThreadFacts
from daily_tasks.core.communications.types import FetchBatch, MatchedLink, MessageMatch, Signal, SignalKind

__all__ = [
    "DEFAULT_INITIAL_LOOKBACK_DAYS",
    "LINK_CONFIDENCE",
    "MIN_LINK_CONFIDENCE",
    "Attachment",
    "CommunicationClient",
    "CommunicationMessage",
    "CursorStore",
    "FetchBatch",
    "FetchCursor",
    "FetchCursors",
    "FetchWindow",
    "ForReviewMessage",
    "MatchedLink",
    "MessageAddress",
    "MessageFacts",
    "MessageGraph",
    "MessageGraphContext",
    "MessageGraphDerived",
    "MessageGraphIndex",
    "MessageGraphRecord",
    "MessageGraphSummary",
    "MessageLink",
    "MessageLog",
    "MessageLogEntry",
    "MessageMatch",
    "MessageSourceStatus",
    "MessageSourceTree",
    "MessageThread",
    "Signal",
    "SignalKind",
    "Suggestion",
    "SuggestionKind",
    "SuggestionTarget",
    "SuggestionValidation",
    "Suggestions",
    "SuggestionsRepository",
    "ThreadFacts",
    "build_message_graph",
    "compute_fetch_window",
    "detect_signals",
    "find_record_mentions",
    "generate_suggestions",
    "ingest_harness_messages",
    "match_messages",
    "normalize_text",
]
