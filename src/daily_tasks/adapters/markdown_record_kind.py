# Responsibility: Classify a vault-relative Markdown path as a project, milestone, task or blocker record.
# Public interface:
# +-- MarkdownRecordKind
# `-- markdown_record_kind(path)
"""File-name conventions of the project vault (`docs/PLANNING_SESSION_CONCEPT.md`, Storage)."""

import re
from pathlib import PurePosixPath
from typing import Final, Literal

type MarkdownRecordKind = Literal["project", "milestone", "task", "blocker"]

_MILESTONE: Final = re.compile(r"^m\d{1,2}(?:\.\d+)?-.+\.md$", re.IGNORECASE)
_MILESTONE_DIR: Final = re.compile(r"^m\d{1,2}(?:\.\d+)?-", re.IGNORECASE)
_TASK: Final = re.compile(r"^t\d+-.+\.md$", re.IGNORECASE)
_BLOCKER: Final = re.compile(r"^b\d+-.+\.md$", re.IGNORECASE)
_DATED: Final = re.compile(r"^\d{4}\.\d{2}\.\d{2}-")
_EXCLUDED_NAMES: Final = frozenset({"definition-of-done.md", "readme.md", "index.md", "job-research-coverage.md"})
_NON_PROJECT_DIRS: Final = frozenset({"applications", "email-opportunities", "opportunities"})


def markdown_record_kind(path: PurePosixPath) -> MarkdownRecordKind | None:
    """Return the record kind its file name implies, or None for any other Markdown file.

    `project-index.md` is a project; `blockers/b<N>-*.md` a blocker; `m<N>-*/milestone.md` or
    `m<N>-*/m<N>-*.md` (the file named after its folder) a milestone; any other `t<N>-*.md`
    or task file inside a milestone folder a task.
    """
    name = path.name
    parent = path.parent.name
    grandparent = path.parent.parent.name if len(path.parts) >= 3 else ""

    if name == "project-index.md":
        return "project"
    if grandparent in _NON_PROJECT_DIRS or parent in _NON_PROJECT_DIRS:
        return None
    if parent == "blockers":
        return "blocker" if _BLOCKER.match(name) else None
    if (name.lower() == "milestone.md" and _MILESTONE_DIR.match(parent)) or (
        _MILESTONE.match(name) and path.stem == parent
    ):
        return "milestone"
    if _TASK.match(name):
        return "task"
    if _MILESTONE_DIR.match(parent):
        if name.lower() in _EXCLUDED_NAMES or _DATED.match(name):
            return None
        return "task"
    return None
