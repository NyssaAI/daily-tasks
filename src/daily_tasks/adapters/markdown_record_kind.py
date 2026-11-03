# Responsibility: Classify a vault-relative Markdown path as a project, milestone, task or blocker record.
# Public interface:
# +-- MarkdownRecordKind
# `-- markdown_record_kind(path)
"""File-name conventions of the project vault (`docs/PLANNING_SESSION_CONCEPT.md`, Storage)."""

import re
from pathlib import PurePosixPath
from typing import Final, Literal

type MarkdownRecordKind = Literal["project", "milestone", "task", "blocker"]

_MILESTONE: Final = re.compile(r"^m\d+(?:\.\d+)?-.+\.md$", re.IGNORECASE)
_TASK: Final = re.compile(r"^t\d+-.+\.md$", re.IGNORECASE)
_BLOCKER: Final = re.compile(r"^b\d+-.+\.md$", re.IGNORECASE)


def markdown_record_kind(path: PurePosixPath) -> MarkdownRecordKind | None:
    """Return the record kind its file name implies, or None for any other Markdown file.

    `project-index.md` is a project; `blockers/b<N>-*.md` a blocker; `m<N>-*/m<N>-*.md` (the file
    named after its folder) a milestone; any other `t<N>-*.md` a task.
    """
    name = path.name
    parent = path.parent.name
    if name == "project-index.md":
        return "project"
    if parent == "blockers":
        return "blocker" if _BLOCKER.match(name) else None
    if _MILESTONE.match(name) and path.stem == parent:
        return "milestone"
    if _TASK.match(name):
        return "task"
    return None
