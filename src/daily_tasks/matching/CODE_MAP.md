# Code Map: `matching`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../server/planning_tools.py`](../server/planning_tools.py) -> `planning_tools`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose deterministic message pre-matching, signal detection and draft suggestion generation.
* **Ubiquitous Language Concepts**: [`Suggestion`](../../../docs/GLOSSARY.md)

```text
__init__.py
`-- (no public symbols)

build_message_graph.py
`-- def build_message_graph( graph: StateGraph, matches: Sequence[MessageMatch], messages_root: str, built_at: datetime, sources: Sequence[MessageSourceStatus], ) -> MessageGraph

detect_signals.py
|-- SIGNAL_PHRASES: Final[Mapping[str, SignalKind]]
`-- def detect_signals(text: str) -> tuple[Signal, ...]

find_record_mentions.py
`-- def find_record_mentions(graph: StateGraph, message: Message) -> Iterator[tuple[UUID, tuple[str, str, str]]]

generate_suggestions.py
|-- MIN_LINK_CONFIDENCE: Final[float]
`-- def generate_suggestions( graph: StateGraph, matches: Sequence[MessageMatch], session_id: UUID, workspace_root: str, clock: Callable[[], datetime], new_id: Callable[[], UUID], definitions_of_done: Mapping[UUID, Sequence[DodItem]] = _NO_DOD, ) -> Suggestions

match_messages.py
|-- LINK_CONFIDENCE: Final[Mapping[str, float]]
`-- def match_messages( graph: StateGraph, messages: Sequence[Message], processed_ids: Collection[str] ) -> tuple[MessageMatch, ...]

normalize_text.py
`-- def normalize_text(text: str) -> str

types.py
|-- class MatchedLink
|-- class MessageMatch
`-- class Signal
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
