"""Responsibility: Prove messages are linked to tasks and blockers by deterministic, scored rules.
Public interface:
+-- BACKGROUND_TASK
+-- GMAIL_TASK
+-- SLACK_TASK
+-- VENDOR_BLOCKER
+-- test_match_messages_known_thread_and_assignee_sender_link_with_reasoning()
+-- test_match_messages_normalized_title_substring_links_task_and_blocker()
+-- test_match_messages_processed_and_repeated_messages_are_dropped()
+-- test_match_messages_record_id_in_body_links_with_full_confidence()
+-- test_match_messages_ref_comment_in_subject_links_record()
+-- test_match_messages_same_input_returns_identical_output()
+-- test_match_messages_sender_assigned_many_tasks_only_corroborates()
+-- test_match_messages_sender_assigned_one_open_task_links_weakly()
+-- test_match_messages_title_inside_longer_word_does_not_match()
+-- test_match_messages_unknown_record_id_is_ignored()
`-- test_match_messages_wiki_link_to_record_file_corroborated_by_title()

Message correlation by record id, wiki link, title, thread and assignee.
"""

from uuid import UUID

from matching_fixtures import message, state_graph

from daily_tasks.matching import LINK_CONFIDENCE, match_messages

GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
SLACK_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000014")
BACKGROUND_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000004")
VENDOR_BLOCKER = UUID("019a4b2c-1f00-7a10-8000-000000000016")


def _links(
    body: str, sender: str = "dana@example.com", **fields: str
) -> list[tuple[str, UUID, tuple[str, ...], float]]:
    (match,) = match_messages(state_graph(), [message("chat:1", body, sender=sender, **fields)], ())
    return [(item.link.record_type, item.link.record_id, item.link.reasons, item.confidence) for item in match.links]


def test_match_messages_record_id_in_body_links_with_full_confidence() -> None:
    links = _links("Closing 019a4b2c-1f00-7a10-8000-000000000014 today")

    assert links == [("task", SLACK_TASK, ("id-match",), 1.0)]


def test_match_messages_ref_comment_in_subject_links_record() -> None:
    links = _links("see subject", subject="Re: <!-- ref: 019a4b2c-1f00-7a10-8000-000000000016 -->")

    assert links == [("blocker", VENDOR_BLOCKER, ("id-match",), 1.0)]


def test_match_messages_unknown_record_id_is_ignored() -> None:
    assert _links("Ref 019a4b2c-1f00-7a10-8000-0000000000ff please") == []


def test_match_messages_wiki_link_to_record_file_corroborated_by_title() -> None:
    links = _links("[[t1-wire-gmail-connector|Wire Gmail connector]] is done")

    assert links == [("task", GMAIL_TASK, ("wiki-link", "title-match"), 0.95)]


def test_match_messages_normalized_title_substring_links_task_and_blocker() -> None:
    links = _links("Slack-connector: waiting on the VENDOR contract   signature!")

    assert links == [
        ("blocker", VENDOR_BLOCKER, ("title-match",), LINK_CONFIDENCE["title-match"]),
        ("task", SLACK_TASK, ("title-match",), LINK_CONFIDENCE["title-match"]),
    ]


def test_match_messages_title_inside_longer_word_does_not_match() -> None:
    assert _links("The slack connectors repo moved") == []


def test_match_messages_known_thread_and_assignee_sender_link_with_reasoning() -> None:
    (match,) = match_messages(
        state_graph(),
        [message("gmail:1", "Scopes are in.", sender="sarah@example.com", thread_id="gmail-thread:18f2a9c3e4b50000")],
        (),
    )

    (link,) = match.links
    assert (link.link.record_id, link.link.reasons, link.confidence) == (
        GMAIL_TASK,
        ("thread-seen-before", "sender-is-assignee"),
        0.65,
    )
    assert link.reasoning == (
        "thread gmail-thread:18f2a9c3e4b50000 was linked to this record before; "
        "sender sarah@example.com is the task assignee"
    )


def test_match_messages_sender_assigned_one_open_task_links_weakly() -> None:
    assert _links("morning!", sender="alex@example.com") == [
        ("task", BACKGROUND_TASK, ("sender-is-assignee",), LINK_CONFIDENCE["sender-is-assignee"])
    ]


def test_match_messages_sender_assigned_many_tasks_only_corroborates() -> None:
    links = _links("Slack connector update", sender="jordan@example.com")

    assert links == [("task", SLACK_TASK, ("title-match", "sender-is-assignee"), 0.75)]


def test_match_messages_processed_and_repeated_messages_are_dropped() -> None:
    messages = [
        message("chat:3", "c", received_at="2026-11-03T12:03:00Z"),
        message("chat:1", "a", received_at="2026-11-03T12:01:00Z"),
        message("chat:2", "b", received_at="2026-11-03T12:02:00Z"),
        message("chat:3", "c again", received_at="2026-11-03T12:03:00Z"),
    ]

    matches = match_messages(state_graph(), messages, {"chat:2"})

    assert [match.message.id for match in matches] == ["chat:1", "chat:3"]
    assert matches[1].message.body == "c"


def test_match_messages_same_input_returns_identical_output() -> None:
    messages = [message("chat:1", "Slack connector merged, vendor contract signature resolved")]

    assert match_messages(state_graph(), messages, ()) == match_messages(state_graph(), messages, ())
