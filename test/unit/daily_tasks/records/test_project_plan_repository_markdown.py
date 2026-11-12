"""Responsibility: Prove ProjectPlanRepositoryMarkdown discovers and parses vault records and skips bad ones.
Public interface:
+-- MILESTONE
+-- PROJECT
+-- test_fetch_projects_attachment_folders_are_not_read(tmp_path, folder, log_capture)
+-- test_fetch_projects_malformed_record_is_skipped_with_warning(tmp_path, log_capture)
+-- test_fetch_projects_missing_root_returns_not_found(tmp_path, log_capture)
+-- test_fetch_projects_record_without_owner_inherits_project_owner(tmp_path)
+-- test_fetch_projects_repository_tree_reads_tasks_and_skips_unsupported_blocker(tmp_path, log_capture)
+-- test_fetch_projects_sample_vault_returns_every_record_kind(tmp_path, log_capture)
`-- test_project_plan_repository_markdown_relative_root_raises()

Project plan reads from Markdown vault trees built in `tmp_path` from the canonical samples.
"""

import asyncio
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok

from conftest import SAMPLES_ROOT, LogCapture
from daily_tasks.core.records import ProjectPlanRepository, ProjectPlanSnapshot
from daily_tasks.records import ProjectPlanRepositoryMarkdown

PROJECT = "2026.10.20-daily-tasks-mcp-server"
MILESTONE = f"{PROJECT}/m2-planning-session-spike"


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def _sample(name: str) -> str:
    return (SAMPLES_ROOT / name).read_text(encoding="utf-8")


def _vault(root: Path) -> Path:
    _write(root, f"{PROJECT}/project-index.md", _sample("5-sample-project-index.md"))
    _write(root, f"{MILESTONE}/m2-planning-session-spike.md", _sample("6-sample-milestone.md"))
    _write(root, f"{MILESTONE}/t1-wire-gmail-connector.md", _sample("4-sample-task.md"))
    _write(root, f"{PROJECT}/blockers/b1-google-oauth-app-verification.md", _sample("7-sample-blocker.md"))
    return root


def _fetch(root: Path) -> ProjectPlanSnapshot:
    repo: ProjectPlanRepository = ProjectPlanRepositoryMarkdown(root, "markdown-projects")
    result = asyncio.run(repo.fetch_projects())
    assert isinstance(result, Ok)
    return result.value


def test_fetch_projects_sample_vault_returns_every_record_kind(tmp_path: Path, log_capture: LogCapture) -> None:
    snapshot = _fetch(_vault(tmp_path))

    assert [p.path for p in snapshot.projects] == [f"{PROJECT}/project-index.md"]
    assert [m.path for m in snapshot.milestones] == [f"{MILESTONE}/m2-planning-session-spike.md"]
    assert [t.path for t in snapshot.tasks] == [f"{MILESTONE}/t1-wire-gmail-connector.md"]
    assert [b.number for b in snapshot.blockers] == [1]
    assert {p.source for p in snapshot.projects} | {t.source for t in snapshot.tasks} == {"markdown-projects"}
    info = [fields for level, _, fields in log_capture.records if level == "info"]
    assert info[0]["task"] == 1
    assert info[0]["skipped"] == 0
    assert not [r for r in log_capture.records if r[0] == "warn"]


def test_fetch_projects_record_without_owner_inherits_project_owner(tmp_path: Path) -> None:
    _vault(tmp_path)
    task = _sample("4-sample-task.md").replace('owner: "jordan@example.com"\n', "")
    _write(tmp_path, f"{MILESTONE}/t2-no-owner.md", task.replace("000000000003\n", "000000000013\n", 1))

    snapshot = _fetch(tmp_path)

    inherited = next(t for t in snapshot.tasks if t.path.endswith("t2-no-owner.md"))
    assert inherited.owner == snapshot.milestones[0].owner


def test_fetch_projects_malformed_record_is_skipped_with_warning(tmp_path: Path, log_capture: LogCapture) -> None:
    _vault(tmp_path)
    _write(tmp_path, f"{MILESTONE}/t2-broken.md", "---\nid: 1\n")
    _write(tmp_path, f"{MILESTONE}/t3-invalid.md", "---\ntype: task\n---\n# Missing fields\n")

    snapshot = _fetch(tmp_path)

    assert len(snapshot.tasks) == 1
    warnings = [(fields["path"], fields["code"]) for level, _, fields in log_capture.records if level == "warn"]
    assert warnings == [
        (f"{MILESTONE}/t2-broken.md", "unclosed-frontmatter"),
        (f"{MILESTONE}/t3-invalid.md", "invalid-record"),
    ]
    assert [(m.path, m.code) for m in snapshot.malformed_records] == [
        (f"{MILESTONE}/t2-broken.md", "unclosed-frontmatter"),
        (f"{MILESTONE}/t3-invalid.md", "invalid-record"),
    ]


@pytest.mark.parametrize("folder", ["inputs", "outputs", ".trash"])
def test_fetch_projects_attachment_folders_are_not_read(
    tmp_path: Path, folder: str, log_capture: LogCapture
) -> None:
    _vault(tmp_path)
    _write(tmp_path, f"{MILESTONE}/{folder}/t9-copy.md", "---\nid: 1\n")

    snapshot = _fetch(tmp_path)

    assert len(snapshot.tasks) == 1
    assert not [r for r in log_capture.records if r[0] == "warn"]


def test_fetch_projects_repository_tree_reads_tasks_and_skips_unsupported_blocker(
    tmp_path: Path, log_capture: LogCapture
) -> None:
    root = _vault(tmp_path / "1-projects")
    _write(
        root,
        f"{PROJECT}/blockers/b1-gmail-oauth-credentials-provisioning.md",
        "---\nid: 019a4b2c-2000-7000-8000-000000000017\ntype: blocker\nstate: active\nblocks:\n  - 1\n---\n# B1\n",
    )

    snapshot = _fetch(root)

    assert [p.title for p in snapshot.projects] == ["Daily Tasks MCP Server"]
    assert len(snapshot.tasks) == sum(1 for _ in root.rglob("t*-*.md"))
    assert snapshot.milestones
    assert "blockers/b1-gmail-oauth-credentials-provisioning.md" in str(
        [fields["path"] for level, _, fields in log_capture.records if level == "warn"]
    )


def test_fetch_projects_missing_root_returns_not_found(tmp_path: Path, log_capture: LogCapture) -> None:
    repo = ProjectPlanRepositoryMarkdown(tmp_path / "missing", "markdown-projects")

    result = asyncio.run(repo.fetch_projects())

    assert isinstance(result, Err)
    assert str(result.category) == "NotFound"
    assert [(level, fields["category"]) for level, _, fields in log_capture.records] == [("error", "NotFound")]


def test_project_plan_repository_markdown_relative_root_raises() -> None:
    with pytest.raises(ValueError, match="absolute"):
        ProjectPlanRepositoryMarkdown(Path("1-projects"), "markdown-projects")
