# Responsibility: Prove the three planning screens render the numbered rows recorded in the session.
# Public interface:
# (none)
"""Markdown output of render_plan_the_day, render_assign_days and render_confirm_plan."""

from datetime import UTC, datetime
from uuid import UUID

from nyssa_ai_result import Ok, Result
from pydantic import TypeAdapter

from conftest import load_spec
from daily_tasks.domain import StateGraph, Suggestions
from daily_tasks.session import (
    SessionState,
    finish_assign_days,
    next_project,
    render_assign_days,
    render_confirm_plan,
    render_plan_the_day,
    review_projects,
    start_session,
)

NOW = datetime(2026, 11, 3, 14, 2, tzinfo=UTC)


def _value(result: Result[SessionState]) -> SessionState:
    assert isinstance(result, Ok), result
    return result.value


def _started(with_suggestions: bool = True) -> SessionState:
    graph = TypeAdapter(StateGraph).validate_python(load_spec("state-graph.json"))
    suggestions = TypeAdapter(Suggestions).validate_python(load_spec("suggestions.json")).suggestions
    initial = SessionState.initial(
        state_graph=graph,
        suggestions=suggestions if with_suggestions else (),
        session_id=UUID("019a4b2c-9000-7000-8000-0000000000a1"),
        workspace_root="D:/vaults/work",
        suggestions_file=".nyssa-ai/daily-tasks/suggestions.json",
        focus=None,
        now=NOW,
    )
    return _value(start_session(initial, None, NOW))


def _row(markdown: str, number: int) -> str:
    return next(line for line in markdown.splitlines() if line.startswith(f"| {number} |"))


def test_render_plan_the_day_shows_plan_and_suggestion_rows() -> None:
    markdown = render_plan_the_day(_started())

    assert "**Open projects: 2**" in markdown
    assert "Tuesday 2026.11.03 · America/Chicago" in markdown
    assert _row(markdown, 1).startswith(
        "| 1 | [>] | Daily Tasks MCP Server | Planning session spike | ↺ Wire Gmail connector <!-- ref: "
    )
    assert _row(markdown, 1).endswith("| jordan@example.com | sarah@example.com | 2026.11.05 |")
    assert _row(markdown, 3).startswith("| 3 | Status | Daily Tasks MCP Server | Planning session spike |")
    assert "| state not-started | state in-progress |" in _row(markdown, 3)
    assert _row(markdown, 4).startswith("| 4 | Blocker | — | — | — <!-- ref: ")
    assert markdown.rstrip().endswith("or keep updating the items above.")


def test_render_plan_the_day_without_suggestions_omits_section() -> None:
    markdown = render_plan_the_day(_started(with_suggestions=False))

    assert "Suggested Updates" not in markdown
    assert "accept" not in markdown


def test_render_assign_days_shows_milestones_tasks_and_blockers() -> None:
    markdown = render_assign_days(_value(review_projects(_started(), NOW)))

    assert markdown.startswith("**Project 1 of 2** · Tuesday 2026.11.03 · America/Chicago")
    assert "## Daily Tasks MCP Server" in markdown
    assert "  - M1: Design (complete)" in markdown
    assert "## M2: Planning session spike" in markdown
    assert "## M3: Connectors" in markdown
    assert "## M4" not in markdown
    assert _row(markdown, 5).endswith(
        "| [>] | sarah@example.com | 2026.11.05 | **Today** | ⛔ #12 Google OAuth app verification |"
    )
    assert _row(markdown, 6).endswith("| **Today** | waits on #5 |")
    assert _row(markdown, 7).endswith("| **Thu 2026.11.05** | ⛔ #12 Google OAuth app verification |")
    assert _row(markdown, 12) == (
        "| 12 | [ ] | Google OAuth app verification <!-- ref: 019a4b2c-1f00-7a10-8000-000000000005 --> "
        "| #5, #7 | jordan@example.com | **Today** |"
    )
    assert '**Next project?** Reply "next"' in markdown


def test_render_assign_days_last_project_asks_to_finalize() -> None:
    markdown = render_assign_days(_value(next_project(_value(review_projects(_started(), NOW)), NOW)))

    assert markdown.startswith("**Project 2 of 2**")
    assert _row(markdown, 13).startswith("| 13 | Token refresh fix <!-- ref: ")
    assert "**Ready to finalize today's plan?**" in markdown


def test_render_assign_days_before_screen_two_is_empty() -> None:
    assert render_assign_days(_started()) == ""


def test_render_confirm_plan_groups_rows_numbered_from_one() -> None:
    state = _value(finish_assign_days(_value(review_projects(_started(), NOW)), NOW))

    markdown = render_confirm_plan(state)

    assert "**Daily plan — Tuesday 2026.11.03** · America/Chicago" in markdown
    assert "**Planned today: 3**          **Mine: 1**          **Delegated: 2**          **Late: 0**" in markdown
    assert "⚠ **2 suggestions still unanswered.**" in markdown
    my_work, delegated = markdown.split("## Delegated work")
    assert "| 1 | [ ] | Daily Tasks MCP Server | Planning session spike | Review Slack connector PR" in my_work
    assert _row(delegated, 2).endswith("| sarah@example.com | 2026.11.05 | ⛔ Google OAuth app verification |")
    assert _row(delegated, 3).endswith("| alex@example.com | — | waits on #2 |")
    assert "#2 Wire Gmail connector | jordan@example.com |" in _row(markdown, 4)
    assert markdown.rstrip().endswith("**Confirm today's plan?**")
