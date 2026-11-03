# Responsibility: Prove MarkdownProjectPlanAdapter discovers and parses vault records and skips bad ones.
# Public interface:
# (none)
"""Project plan reads from Markdown vault trees built in `tmp_path` from the canonical samples."""

import asyncio
import shutil
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

import pytest
from nyssa_ai_result import Err, Ok

from conftest import SPECS_ROOT
from daily_tasks.adapters.markdown_project_plan_adapter import MarkdownProjectPlanAdapter
from daily_tasks.ports import ProjectPlanPort, ProjectPlanSnapshot

PROJECT = "2026.10.20-daily-tasks-mcp-server"
MILESTONE = f"{PROJECT}/m2-planning-session-spike"
REPO_PROJECTS = Path(__file__).resolve().parents[4] / "projects"


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


def _write(root: Path, relative: str, text: str) -> None:
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="")


def _sample(name: str) -> str:
    return (SPECS_ROOT / name).read_text(encoding="utf-8")


def _vault(root: Path) -> Path:
    _write(root, f"{PROJECT}/project-index.md", _sample("5-sample-project-index.md"))
    _write(root, f"{MILESTONE}/m2-planning-session-spike.md", _sample("6-sample-milestone.md"))
    _write(root, f"{MILESTONE}/t1-wire-gmail-connector.md", _sample("4-sample-task.md"))
    _write(root, f"{PROJECT}/blockers/b1-google-oauth-app-verification.md", _sample("7-sample-blocker.md"))
    return root


def _fetch(root: Path, logger: _RecordingLogger) -> ProjectPlanSnapshot:
    port: ProjectPlanPort = MarkdownProjectPlanAdapter(root, "markdown-projects", logger)
    result = asyncio.run(port.fetch_projects())
    assert isinstance(result, Ok)
    return result.value


def test_fetch_projects_sample_vault_returns_every_record_kind(tmp_path: Path) -> None:
    logger = _RecordingLogger()

    snapshot = _fetch(_vault(tmp_path), logger)

    assert [p.path for p in snapshot.projects] == [f"{PROJECT}/project-index.md"]
    assert [m.path for m in snapshot.milestones] == [f"{MILESTONE}/m2-planning-session-spike.md"]
    assert [t.path for t in snapshot.tasks] == [f"{MILESTONE}/t1-wire-gmail-connector.md"]
    assert [b.number for b in snapshot.blockers] == [1]
    assert {r.source for r in (*snapshot.projects, *snapshot.tasks)} == {"markdown-projects"}
    info = [fields for level, _, fields in logger.records if level == "info"]
    assert info[0]["task"] == 1
    assert info[0]["skipped"] == 0
    assert not [r for r in logger.records if r[0] == "warn"]


def test_fetch_projects_record_without_owner_inherits_project_owner(tmp_path: Path) -> None:
    _vault(tmp_path)
    task = _sample("4-sample-task.md").replace('owner: "jordan@example.com"\n', "")
    _write(tmp_path, f"{MILESTONE}/t2-no-owner.md", task.replace("000000000003\n", "000000000013\n", 1))

    snapshot = _fetch(tmp_path, _RecordingLogger())

    inherited = next(t for t in snapshot.tasks if t.path.endswith("t2-no-owner.md"))
    assert inherited.owner == snapshot.milestones[0].owner


def test_fetch_projects_malformed_record_is_skipped_with_warning(tmp_path: Path) -> None:
    _vault(tmp_path)
    _write(tmp_path, f"{MILESTONE}/t2-broken.md", "---\nid: 1\n")
    _write(tmp_path, f"{MILESTONE}/t3-invalid.md", "---\ntype: task\n---\n# Missing fields\n")
    logger = _RecordingLogger()

    snapshot = _fetch(tmp_path, logger)

    assert len(snapshot.tasks) == 1
    warnings = [(fields["path"], fields["code"]) for level, _, fields in logger.records if level == "warn"]
    assert warnings == [
        (f"{MILESTONE}/t2-broken.md", "unclosed-frontmatter"),
        (f"{MILESTONE}/t3-invalid.md", "invalid-record"),
    ]
    assert [(m.path, m.code) for m in snapshot.malformed_records] == [
        (f"{MILESTONE}/t2-broken.md", "unclosed-frontmatter"),
        (f"{MILESTONE}/t3-invalid.md", "invalid-record"),
    ]


@pytest.mark.parametrize("folder", ["inputs", "outputs", ".trash"])
def test_fetch_projects_attachment_folders_are_not_read(tmp_path: Path, folder: str) -> None:
    _vault(tmp_path)
    _write(tmp_path, f"{MILESTONE}/{folder}/t9-copy.md", "---\nid: 1\n")
    logger = _RecordingLogger()

    snapshot = _fetch(tmp_path, logger)

    assert len(snapshot.tasks) == 1
    assert not [r for r in logger.records if r[0] == "warn"]


def test_fetch_projects_repository_tree_reads_tasks_and_skips_unsupported_blocker(tmp_path: Path) -> None:
    root = tmp_path / "projects"
    shutil.copytree(REPO_PROJECTS, root)
    logger = _RecordingLogger()

    snapshot = _fetch(root, logger)

    assert [p.title for p in snapshot.projects] == ["Daily Tasks Python MCP Server"]
    assert len(snapshot.tasks) == sum(1 for _ in root.rglob("t*-*.md"))
    assert snapshot.milestones
    assert "blockers/b1-gmail-oauth-credentials-provisioning.md" in str(
        [fields["path"] for level, _, fields in logger.records if level == "warn"]
    )


def test_fetch_projects_missing_root_returns_not_found(tmp_path: Path) -> None:
    logger = _RecordingLogger()
    adapter = MarkdownProjectPlanAdapter(tmp_path / "missing", "markdown-projects", logger)

    result = asyncio.run(adapter.fetch_projects())

    assert isinstance(result, Err)
    assert str(result.category) == "NotFound"
    assert [(level, fields["category"]) for level, _, fields in logger.records] == [("error", "NotFound")]


def test_markdown_project_plan_adapter_relative_root_raises() -> None:
    with pytest.raises(ValueError, match="absolute"):
        MarkdownProjectPlanAdapter(Path("projects"), "markdown-projects", _RecordingLogger())
