# Responsibility: Verify the daily plan renderer matches the sample and round-trips through the parser.
# Public interface:
# (none)
"""Render `daily-plan.json` to `8-sample-daily-plan.md` and parse it back."""

from dataclasses import replace
from datetime import date

from nyssa_ai_result import Err, Ok
from pydantic import TypeAdapter

from conftest import SPECS_ROOT, load_spec
from daily_tasks.domain import DailyPlan
from daily_tasks.storage.cst import (
    DailyPlanDocument,
    PlanBlockerView,
    PlanItemView,
    RecordLocation,
    parse_daily_plan,
    parse_markdown,
    render_daily_plan,
)

PROJECT = "projects/2026.10.20-daily-tasks-mcp-server/"
SPIKE = "Planning session spike"
SERVER = "Daily Tasks MCP Server"


def _sample_text() -> str:
    return (SPECS_ROOT / "8-sample-daily-plan.md").read_text(encoding="utf-8", newline="")


def _sample_plan() -> DailyPlan:
    return TypeAdapter(DailyPlan).validate_python(load_spec("daily-plan.json"))


def _sample_document() -> DailyPlanDocument:
    items = (
        PlanItemView(
            item_id="019a4b2c-1f00-7a10-8000-000000000008",
            title="Review Slack connector PR",
            path=PROJECT + "m2-planning-session-spike/t4-review-slack-connector-pr",
            project_title=SERVER,
            milestone_title=SPIKE,
            status_mark=" ",
            due_date=date(2026, 11, 5),
        ),
        PlanItemView(
            item_id="019a4b2c-1f00-7a10-8000-000000000003",
            title="Wire Gmail connector behind Communication-Port",
            path=PROJECT + "m2-planning-session-spike/t1-wire-gmail-connector",
            project_title=SERVER,
            milestone_title=SPIKE,
            status_mark=" ",
            due_date=date(2026, 11, 5),
        ),
        PlanItemView(
            item_id="019a4b2c-1f00-7a10-8000-000000000004",
            title="Background fetch survives turns",
            path=PROJECT + "m2-planning-session-spike/t2-background-fetch-survives-turns",
            project_title=SERVER,
            milestone_title=SPIKE,
            status_mark=" ",
            due_date=None,
        ),
    )
    blockers = (
        PlanBlockerView(
            blocker_id="019a4b2c-1f00-7a10-8000-000000000005",
            title="Google OAuth app verification",
            path=PROJECT + "blockers/b1-google-oauth-app-verification",
            impact="Gmail connector can't be tested outside the dev account.",
            owner="jordan@example.com",
            resolved_when="Google approves the OAuth app.",
        ),
    )
    return DailyPlanDocument(
        plan=_sample_plan(),
        owner="jordan@example.com",
        tags=("plan", "daily"),
        maturity="reviewed",
        record_version=2,
        items=items,
        blockers=blockers,
    )


def test_render_daily_plan_sample_matches_sample_markdown() -> None:
    document = _sample_document()

    text = render_daily_plan(document)

    assert text.replace("\r\n", "\n") == _sample_text().replace("\r\n", "\n")


def test_parse_daily_plan_sample_with_stored_plan_returns_equal_plan() -> None:
    stored = _sample_plan()
    markdown = parse_markdown(_sample_text()).unwrap()

    result = parse_daily_plan(markdown, RecordLocation(path=stored.path, source=stored.source), stored)

    assert isinstance(result, Ok)
    assert result.value.plan.content_hash.startswith("sha256:")
    assert replace(result.value.plan, content_hash=stored.content_hash) == stored
    assert result.value == replace(_sample_document(), plan=result.value.plan)


def test_render_then_parse_round_trip_keeps_shown_values() -> None:
    document = _sample_document()
    location = RecordLocation(path=document.plan.path, source=document.plan.source)

    parsed = parse_daily_plan(parse_markdown(render_daily_plan(document)).unwrap(), location)

    assert isinstance(parsed, Ok)
    plan = parsed.value.plan
    assert parsed.value.items == document.items
    assert parsed.value.blockers == document.blockers
    assert (plan.focus, plan.summary, plan.decisions) == (
        document.plan.focus,
        document.plan.summary,
        document.plan.decisions,
    )
    assert plan.blockers == document.plan.blockers
    assert [(str(e.item_id), e.section) for e in plan.entries] == [
        ("019a4b2c-1f00-7a10-8000-000000000008", "my-work"),
        ("019a4b2c-1f00-7a10-8000-000000000003", "delegated-work"),
        ("019a4b2c-1f00-7a10-8000-000000000004", "delegated-work"),
    ]


def test_render_daily_plan_escapes_pipes_in_table_cells() -> None:
    sample = _sample_document()
    item = replace(sample.items[0], title="Fix A|B", project_title="P|Q")
    document = replace(sample, items=(item, *sample.items[1:]))

    text = render_daily_plan(document)

    assert "| P\\|Q | Planning session spike | [[" in text
    assert "\\|Fix A\\|B]] <!-- ref: 019a4b2c-1f00-7a10-8000-000000000008 -->" in text
    reparsed = parse_daily_plan(
        parse_markdown(text).unwrap(), RecordLocation(path=sample.plan.path, source=sample.plan.source)
    )
    assert isinstance(reparsed, Ok)
    assert reparsed.value.items[0] == item


def test_render_daily_plan_without_blockers_or_decisions_shows_empty_sections() -> None:
    sample = _sample_document()
    document = replace(sample, plan=replace(sample.plan, blockers=(), decisions=()))

    text = render_daily_plan(document)

    assert "## Blockers Under Active Resolution\n\nNone\n\n## Decisions\n\n## Notes and references\n" in text


def test_parse_daily_plan_row_without_link_returns_invalid_plan_row() -> None:
    text = _sample_text().replace("[[projects/2026.10.20-daily-tasks-mcp-server/m2-planning-session-spike/t2", "t2")
    markdown = parse_markdown(text).unwrap()

    result = parse_daily_plan(markdown, RecordLocation(path="p.md", source="markdown-daily-plans"))

    assert isinstance(result, Err)
    assert result.error.code == "invalid-plan-row"
