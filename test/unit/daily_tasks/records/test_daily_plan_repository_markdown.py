"""Responsibility: Prove DailyPlanRepositoryMarkdown selects the plans nearest a date and skips bad files.
Public interface:
+-- SAMPLE_DATE
+-- test_fetch_plans_around_date_returns_that_day_and_latest_earlier(tmp_path, around, expected)
+-- test_fetch_plans_malformed_plan_is_skipped_with_warning(tmp_path, log_capture)
+-- test_fetch_plans_missing_root_returns_not_found(tmp_path, log_capture)
`-- test_fetch_plans_sample_plan_has_folder_relative_path_and_source(tmp_path)

Daily plan reads from a `daily-plans/` folder built in `tmp_path` from the canonical sample.
"""

import asyncio
from datetime import date
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok

from conftest import SAMPLES_ROOT, LogCapture
from daily_tasks.core.records import DailyPlanRepository
from daily_tasks.records import DailyPlanRepositoryMarkdown

SAMPLE_DATE = "2026-11-03"


def _plans_root(tmp_path: Path, *days: str) -> Path:
    root = tmp_path / "daily-plans"
    root.mkdir()
    sample = (SAMPLES_ROOT / "8-sample-daily-plan.md").read_text(encoding="utf-8")
    for day in days:
        text = sample.replace(f'date: "{SAMPLE_DATE}"', f'date: "{day}"')
        (root / f"{day.replace('-', '.')}-daily-plan.md").write_text(text, encoding="utf-8")
    return root


def _dates(root: Path, around: date) -> list[str]:
    repo: DailyPlanRepository = DailyPlanRepositoryMarkdown(root, "markdown-daily-plans")
    result = asyncio.run(repo.fetch_plans(around))
    assert isinstance(result, Ok)
    return [plan.local_date.isoformat() for plan in result.value]


@pytest.mark.parametrize(
    ("around", "expected"),
    [
        (date(2026, 11, 3), ["2026-11-03", "2026-10-30"]),
        (date(2026, 11, 2), ["2026-10-30"]),
        (date(2026, 11, 10), ["2026-11-04"]),
        (date(2026, 10, 1), []),
    ],
)
def test_fetch_plans_around_date_returns_that_day_and_latest_earlier(
    tmp_path: Path, around: date, expected: list[str]
) -> None:
    root = _plans_root(tmp_path, "2026-10-28", "2026-10-30", "2026-11-03", "2026-11-04")

    assert _dates(root, around) == expected


def test_fetch_plans_sample_plan_has_folder_relative_path_and_source(tmp_path: Path) -> None:
    root = _plans_root(tmp_path, SAMPLE_DATE)
    repo = DailyPlanRepositoryMarkdown(root, "markdown-daily-plans")

    result = asyncio.run(repo.fetch_plans(date(2026, 11, 3)))

    assert isinstance(result, Ok)
    plan = result.value[0]
    assert (plan.path, plan.source) == ("daily-plans/2026.11.03-daily-plan.md", "markdown-daily-plans")
    assert plan.focus == "Light day, out after 3pm."


def test_fetch_plans_malformed_plan_is_skipped_with_warning(tmp_path: Path, log_capture: LogCapture) -> None:
    root = _plans_root(tmp_path, "2026-10-28", "2026-10-30")
    (root / "2026.10.30-daily-plan.md").write_text("---\nid: 1\n", encoding="utf-8")
    (root / "notes.md").write_text("# not a plan\n", encoding="utf-8")

    repo = DailyPlanRepositoryMarkdown(root, "markdown-daily-plans")
    result = asyncio.run(repo.fetch_plans(date(2026, 10, 30)))
    assert isinstance(result, Ok)
    assert [plan.local_date.isoformat() for plan in result.value] == ["2026-10-28"]
    warnings = [(fields["path"], fields["code"]) for level, _, fields in log_capture.records if level == "warn"]
    assert warnings == [("2026.10.30-daily-plan.md", "unclosed-frontmatter")]
    assert [(m.path, m.code) for m in repo.malformed_records] == [
        ("daily-plans/2026.10.30-daily-plan.md", "unclosed-frontmatter")
    ]


def test_fetch_plans_missing_root_returns_not_found(tmp_path: Path, log_capture: LogCapture) -> None:
    repo = DailyPlanRepositoryMarkdown(tmp_path / "missing", "markdown-daily-plans")

    result = asyncio.run(repo.fetch_plans(date(2026, 11, 3)))

    assert isinstance(result, Err)
    assert str(result.category) == "NotFound"
    assert [(level, fields["category"]) for level, _, fields in log_capture.records] == [("error", "NotFound")]
