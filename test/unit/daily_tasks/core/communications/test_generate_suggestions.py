"""Responsibility: Prove signals on linked messages become pending, validated draft suggestions.
Public interface:
+-- DOD_ITEM
+-- GMAIL_TASK
+-- SESSION
+-- SLACK_TASK
+-- VENDOR_BLOCKER
+-- test_generate_suggestions_blocked_on_task_with_open_blocker_proposes_nothing()
+-- test_generate_suggestions_can_you_proposes_new_task_for_user()
+-- test_generate_suggestions_done_naming_dod_item_proposes_dod_check()
+-- test_generate_suggestions_merged_on_linked_task_proposes_completion()
+-- test_generate_suggestions_output_round_trips_and_stays_pending()
+-- test_generate_suggestions_stuck_on_unblocked_task_proposes_new_blocker()
+-- test_generate_suggestions_unblocked_on_open_blocker_proposes_resolve()
`-- test_generate_suggestions_weak_assignee_link_or_no_signal_proposes_nothing()

Deterministic draft suggestions: status, dod, blocker and new-task, never accepted.
"""

from collections.abc import Mapping
from uuid import UUID

from matching_fixtures import BUILT_AT, message, sequential_ids, state_graph
from pydantic import TypeAdapter

from daily_tasks.core.communications import (
    CommunicationMessage,
    Suggestions,
    generate_suggestions,
    match_messages,
)
from daily_tasks.core.records import DodItem

SESSION = UUID("019a4b2c-9000-7000-8000-0000000000a1")
SLACK_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000014")
GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
VENDOR_BLOCKER = UUID("019a4b2c-1f00-7a10-8000-000000000016")
DOD_ITEM = UUID("019a4b2c-1f00-7a10-8000-0000000000d4")


def _suggest(*messages: CommunicationMessage, dod: Mapping[UUID, tuple[DodItem, ...]] | None = None) -> Suggestions:
    graph = state_graph()
    return generate_suggestions(
        graph,
        match_messages(graph, messages, ()),
        SESSION,
        "D:/vaults/work",
        lambda: BUILT_AT,
        sequential_ids(),
        dict(dod) if dod is not None else {},
    )


def test_generate_suggestions_merged_on_linked_task_proposes_completion() -> None:
    result = _suggest(message("slack:1", "The Slack connector PR is merged.", sender="dana@example.com"))

    (suggestion,) = result.suggestions
    assert (suggestion.kind, suggestion.target and suggestion.target.record_id) == ("status", SLACK_TASK)
    assert (suggestion.current, suggestion.proposed) == ({"state": "in-progress"}, {"state": "completed"})
    assert suggestion.evidence == "The Slack connector PR is merged"
    assert suggestion.rationale == (
        "message reports 'merged'; linked because message mentions the title 'Slack connector' (confidence 0.70)"
    )
    assert (suggestion.source_message_ids, suggestion.created_in_session) == (("slack:1",), SESSION)
    assert suggestion.id == UUID("019a4b2c-9000-7000-8000-000000000001")
    assert suggestion.validation.ok is False
    assert suggestion.validation.issues == ("definition of done incomplete (0/1)",)


def test_generate_suggestions_done_naming_dod_item_proposes_dod_check() -> None:
    dod = {SLACK_TASK: (DodItem(id=DOD_ITEM, text="Cursor persistence", done=False),)}

    result = _suggest(
        message("slack:1", "Slack connector: cursor persistence is done", sender="dana@example.com"), dod=dod
    )

    (suggestion,) = result.suggestions
    assert suggestion.kind == "dod"
    assert suggestion.proposed == {"dod": {str(DOD_ITEM): True}}


def test_generate_suggestions_unblocked_on_open_blocker_proposes_resolve() -> None:
    result = _suggest(message("gmail:1", "Vendor contract signature arrived, we are unblocked"))

    (suggestion,) = result.suggestions
    assert (suggestion.kind, suggestion.target and suggestion.target.record_id) == ("blocker", VENDOR_BLOCKER)
    assert (suggestion.current, suggestion.proposed) == ({"state": "open"}, {"action": "resolve"})
    assert suggestion.validation.ok


def test_generate_suggestions_stuck_on_unblocked_task_proposes_new_blocker() -> None:
    result = _suggest(message("slack:1", "Slack connector is stuck on rate limits", sender="dana@example.com"))

    (suggestion,) = result.suggestions
    assert suggestion.kind == "blocker"
    assert suggestion.current is None
    assert suggestion.proposed == {
        "action": "create",
        "new_blocker": {"title": "Slack connector is stuck on rate limits", "blocks": [str(SLACK_TASK)]},
    }


def test_generate_suggestions_blocked_on_task_with_open_blocker_proposes_nothing() -> None:
    result = _suggest(message("gmail:1", "Wire Gmail connector still blocked", sender="dana@example.com"))

    assert result.suggestions == ()
    assert result.no_suggestion_message_ids == ("gmail:1",)


def test_generate_suggestions_can_you_proposes_new_task_for_user() -> None:
    result = _suggest(message("slack:1", "@jordan can you review the Slack connector docs?", sender="dana@example.com"))

    (suggestion,) = result.suggestions
    assert (suggestion.kind, suggestion.target) == ("new-task", None)
    assert suggestion.proposed == {
        "title": "@jordan can you review the Slack connector docs",
        "assignee": "jordan@example.com",
        "milestone_id": "019a4b2c-1f00-7a10-8000-000000000012",
    }
    assert suggestion.validation.ok


def test_generate_suggestions_weak_assignee_link_or_no_signal_proposes_nothing() -> None:
    result = _suggest(
        message("slack:1", "all done for today", sender="alex@example.com"),
        message("slack:2", "Slack connector looks good", sender="dana@example.com"),
    )

    assert result.suggestions == ()
    assert result.no_suggestion_message_ids == ("slack:1", "slack:2")


def test_generate_suggestions_output_round_trips_and_stays_pending() -> None:
    result = _suggest(
        message(
            "slack:1", "Slack connector merged. Can you check the vendor contract signature?", sender="dana@example.com"
        ),
    )
    adapter = TypeAdapter(Suggestions)

    assert adapter.validate_json(adapter.dump_json(result)) == result
    assert [item.kind for item in result.suggestions] == ["status", "new-task"]
    assert "accepted" not in adapter.dump_json(result).decode()
    assert result.updated_at == BUILT_AT
