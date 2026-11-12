"""Responsibility: Classify a vault-relative Markdown path as a project, milestone, task, or blocker record.
Public interface:
`-- markdown_record_kind(path)
"""

import re
from pathlib import PurePosixPath
from typing import Final

from daily_tasks.core.records.record_kind import RecordKind

_MILESTONE: Final = re.compile(r"^m\d{1,2}(?:\.\d+)?-.+\.md$", re.IGNORECASE)
_MILESTONE_DIR: Final = re.compile(r"^m\d{1,2}(?:\.\d+)?-", re.IGNORECASE)
_TASK: Final = re.compile(r"^t\d+-.+\.md$", re.IGNORECASE)
_BLOCKER: Final = re.compile(r"^b\d+-.+\.md$", re.IGNORECASE)
_DATED: Final = re.compile(r"^\d{4}\.\d{2}\.\d{2}-")
_EXCLUDED_NAMES: Final = frozenset({"definition-of-done.md", "readme.md", "index.md", "job-research-coverage.md"})
_NON_PROJECT_DIRS: Final = frozenset({"applications", "email-opportunities", "opportunities"})


def markdown_record_kind(path: PurePosixPath) -> RecordKind | None:
    """Return the record kind its file name implies, or None for any other Markdown file."""
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
