# Responsibility: Turn pre-matched messages into pending draft suggestions.
# Public interface:
# +-- MIN_LINK_CONFIDENCE
# `-- generate_suggestions(graph, matches, session_id, workspace_root, clock, new_id, definitions_of_done)
"""Deterministic draft suggestions; every suggestion is pending and nothing is ever accepted here."""

from collections.abc import Callable, Iterator, Mapping, Sequence
from datetime import datetime
from types import MappingProxyType
from typing import Final, Literal
from uuid import UUID

from pydantic import JsonValue

from daily_tasks.domain import DodItem, StateGraph, Suggestion, Suggestions, SuggestionTarget, SuggestionValidation
from daily_tasks.matching.normalize_text import normalize_text
from daily_tasks.matching.types import MatchedLink, MessageMatch, Signal

MIN_LINK_CONFIDENCE: Final[float] = 0.5

type _Kind = Literal["new-task", "status", "dod", "blocker"]
type _Draft = tuple[_Kind, MatchedLink | None, Mapping[str, JsonValue] | None, Mapping[str, JsonValue], str]

_OPEN_TASK: Final[frozenset[str]] = frozenset({"not-started", "in-progress"})
_RESOLVES_BLOCKER: Final[frozenset[str]] = frozenset({"unblocked", "resolved", "done", "completed"})
_COMPLETES_TASK: Final[frozenset[str]] = frozenset({"done", "completed", "merged", "resolved"})
_NO_DOD: Final[Mapping[UUID, Sequence[DodItem]]] = MappingProxyType({})


def _best(match: MessageMatch, record_type: str) -> MatchedLink | None:
    candidates = [item for item in match.links if item.link.record_type == record_type]
    return candidates[0] if candidates and candidates[0].confidence >= MIN_LINK_CONFIDENCE else None


def _task_drafts(
    graph: StateGraph, link: MatchedLink, signal: Signal, dod: Mapping[UUID, Sequence[DodItem]], text: str
) -> Iterator[_Draft]:
    task_id = link.link.record_id
    state = graph.records.tasks[task_id].state
    if signal.kind == "completion" and signal.phrase in _COMPLETES_TASK and state in _OPEN_TASK:
        named = [item for item in dod.get(task_id, ()) if not item.done and normalize_text(item.text) in text]
        if named:
            yield (
                "dod",
                link,
                {"dod": {str(item.id): False for item in named}},
                {"dod": {str(item.id): True for item in named}},
                f"message reports '{signal.phrase}' for Definition of Done items of the task",
            )
        else:
            yield "status", link, {"state": state}, {"state": "completed"}, f"message reports '{signal.phrase}'"
    elif signal.kind == "blocked" and state in _OPEN_TASK:
        blocker = next((b for b in graph.index.blocked_by.get(task_id, ()) if b in graph.records.blockers), None)
        if blocker is not None and graph.records.blockers[blocker].state == "open":
            return
        new_blocker: dict[str, JsonValue] = {"title": signal.quote, "blocks": [str(task_id)]}
        yield "blocker", link, None, {"action": "create", "new_blocker": new_blocker}, f"message says '{signal.phrase}'"


def _drafts(
    graph: StateGraph, match: MessageMatch, dod: Mapping[UUID, Sequence[DodItem]]
) -> Iterator[tuple[_Draft, Signal]]:
    text = f" {normalize_text(match.message.body or match.message.snippet)} "
    task, blocker = _best(match, "task"), _best(match, "blocker")
    for signal in match.signals:
        if signal.kind == "request":
            proposed: dict[str, JsonValue] = {"title": signal.quote, "assignee": graph.context.user.email}
            if task is not None:
                proposed["milestone_id"] = str(graph.records.tasks[task.link.record_id].milestone_id)
            yield ("new-task", None, None, proposed, f"{match.message.sender.address} asks for work"), signal
            continue
        if blocker is not None and signal.kind == "completion" and signal.phrase in _RESOLVES_BLOCKER:
            current = graph.records.blockers[blocker.link.record_id].state
            if current == "open":
                why = f"message says '{signal.phrase}' about the blocker"
                yield ("blocker", blocker, {"state": current}, {"action": "resolve"}, why), signal
                continue
        if task is not None:
            yield from ((draft, signal) for draft in _task_drafts(graph, task, signal, dod, text))


def _validation(
    graph: StateGraph, kind: _Kind, link: MatchedLink | None, proposed: Mapping[str, JsonValue]
) -> SuggestionValidation:
    issues: list[str] = []
    if kind == "new-task" and "milestone_id" not in proposed:
        issues.append("milestone unknown: no linked task to place the new task under")
    if kind == "status" and link is not None:
        facts = graph.derived.tasks.get(link.link.record_id)
        if facts is not None and facts.dod.done < facts.dod.total:
            issues.append(f"definition of done incomplete ({facts.dod.done}/{facts.dod.total})")
    return SuggestionValidation(ok=not issues, issues=tuple(issues))


def generate_suggestions(
    graph: StateGraph,
    matches: Sequence[MessageMatch],
    session_id: UUID,
    workspace_root: str,
    clock: Callable[[], datetime],
    new_id: Callable[[], UUID],
    definitions_of_done: Mapping[UUID, Sequence[DodItem]] = _NO_DOD,
) -> Suggestions:
    """Draft one pending suggestion per (kind, target, proposal) a message's signals imply.

    Completion signals resolve an open linked blocker or complete an open linked task (a `dod` suggestion when
    the message names unchecked Definition of Done items); `blocked` signals propose a new blocker for a linked
    task that has none open; `can you` proposes a new task for the user. Links weaker than `MIN_LINK_CONFIDENCE`
    are ignored. Messages without a suggestion are listed in `no_suggestion_message_ids`.
    """
    now = clock()
    suggestions: list[Suggestion] = []
    silent: list[str] = []
    for match in matches:
        seen: set[str] = set()
        count = len(suggestions)
        for (kind, link, current, proposed, why), signal in _drafts(graph, match, definitions_of_done):
            key = f"{kind}:{link.link.record_id if link else ''}:{sorted(proposed)}"
            if key in seen:
                continue
            seen.add(key)
            target = None
            if link is not None:
                target = SuggestionTarget(
                    record_type=link.link.record_type,
                    record_id=link.link.record_id,
                    expected_updated_at=graph.context.built_at,
                )
            reasoning = f"{why}; linked because {link.reasoning} (confidence {link.confidence:.2f})" if link else why
            suggestions.append(
                Suggestion(
                    id=new_id(),
                    kind=kind,
                    created_at=now,
                    created_in_session=session_id,
                    source_message_ids=(match.message.id,),
                    evidence=signal.quote,
                    rationale=reasoning,
                    target=target,
                    current=current,
                    proposed=proposed,
                    validation=_validation(graph, kind, link, proposed),
                )
            )
        if len(suggestions) == count:
            silent.append(match.message.id)
    return Suggestions(
        workspace_root=workspace_root,
        updated_at=now,
        no_suggestion_message_ids=tuple(silent),
        suggestions=tuple(suggestions),
    )
