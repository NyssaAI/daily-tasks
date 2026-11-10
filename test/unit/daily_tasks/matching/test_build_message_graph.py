"""Responsibility: Prove matched messages project into a MessageGraph that round-trips through the spec DTO.
Public interface:
+-- GMAIL_TASK
+-- SOURCES
+-- THREAD
+-- test_build_message_graph_links_indexed_by_message_and_record()
+-- test_build_message_graph_round_trips_through_json()
+-- test_build_message_graph_summary_counts_linked_and_superseded()
`-- test_build_message_graph_thread_latest_needs_review_earlier_superseded()

Message graph assembly: records, threads, links, review queue and summary.
"""

from uuid import UUID

from matching_fixtures import BUILT_AT, message, state_graph
from pydantic import TypeAdapter

from daily_tasks.domain import MessageGraph, MessageSourceStatus
from daily_tasks.matching import build_message_graph, match_messages

THREAD = "gmail-thread:18f2a9c3e4b50000"
GMAIL_TASK = UUID("019a4b2c-1f00-7a10-8000-000000000003")
SOURCES = (MessageSourceStatus(name="gmail", status="ok", since=BUILT_AT, fetched=3, error=None),)


def _graph() -> MessageGraph:
    graph = state_graph()
    messages = [
        message(
            "gmail:a",
            "Gmail connector scopes PR is up",
            "sarah@example.com",
            THREAD,
            "Gmail connector",
            "2026-11-03T09:15:00Z",
        ),
        message(
            "gmail:b", "Scopes merged.", "sarah@example.com", THREAD, "Re: Gmail connector", "2026-11-03T12:41:09Z"
        ),
        message("slack:c", "lunch?", "dana@example.com", None, None, "2026-11-03T10:00:00Z"),
    ]
    return build_message_graph(graph, match_messages(graph, messages, ()), "D:/inbox", BUILT_AT, SOURCES)


def test_build_message_graph_thread_latest_needs_review_earlier_superseded() -> None:
    derived = _graph().derived

    assert [item.message_id for item in derived.for_review] == ["slack:c", "gmail:b"]
    assert derived.for_review[1].earlier_in_thread == ("gmail:a",)
    assert derived.messages["gmail:a"].superseded_by == "gmail:b"
    assert not derived.messages["gmail:a"].needs_review
    assert not any(facts.reviewed for facts in derived.messages.values())


def test_build_message_graph_links_indexed_by_message_and_record() -> None:
    graph = _graph()

    assert graph.index.by_record[GMAIL_TASK] == ("gmail:a", "gmail:b")
    assert graph.index.links["gmail:b"][0].reasons == ("thread-seen-before", "sender-is-assignee")
    assert "slack:c" not in graph.index.links
    assert graph.derived.threads[THREAD].linked_record_ids == (GMAIL_TASK,)
    assert graph.derived.threads[THREAD].participants == ("sarah@example.com", "jordan@example.com")


def test_build_message_graph_summary_counts_linked_and_superseded() -> None:
    summary = _graph().derived.summary

    assert (summary.fetched_this_run, summary.needs_review, summary.superseded) == (3, 2, 1)
    assert (summary.linked, summary.unlinked) == (2, 1)


def test_build_message_graph_round_trips_through_json() -> None:
    adapter = TypeAdapter(MessageGraph)
    graph = _graph()

    assert adapter.validate_json(adapter.dump_json(graph)) == graph
    assert adapter.dump_python(graph, mode="json")["derived"]["for_review"][1]["links"] == {
        "$ref": "#/index/links/gmail:b"
    }
