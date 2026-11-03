# Responsibility: Map a parsed project index Markdown record onto the Project DTO.
# Public interface:
# `-- parse_project(document, location)
"""Project index parser: frontmatter, description paragraph, milestone headings and blocker table."""

import re
from typing import Final

from nyssa_ai_result import Result
from pydantic import TypeAdapter

from daily_tasks.domain import Project
from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.record_fields import RecordFields
from daily_tasks.storage.cst.types import RecordLocation

_PROJECT: Final[TypeAdapter[Project]] = TypeAdapter(Project)
_DIRECTORY_DATE: Final = re.compile(r"(?:^|/)(\d{4})\.(\d{2})\.(\d{2})-[^/]+/[^/]+$")
_MILESTONE_HEADING: Final = re.compile(r"^\[.\]\s+M\d+:")


def _description(document: MarkdownDocument) -> str | None:
    """First paragraph after the title that is not a bold metadata line."""
    title = next((s for s in document.sections if s.heading.level == 1), None)
    if title is None:
        return None
    end = next(
        (s.heading.line_index for s in document.sections if s.heading.line_index > title.heading.line_index),
        len(document.lines),
    )
    for line in document.lines[title.heading.line_index + 1 : end]:
        text = line.text.strip()
        if text and not text.startswith("**"):
            return text
    return None


def _directory_date(path: str) -> str | None:
    match = _DIRECTORY_DATE.search(path.replace("\\", "/"))
    return f"{match.group(1)}-{match.group(2)}-{match.group(3)}" if match else None


def parse_project(document: MarkdownDocument, location: RecordLocation) -> Result[Project, ParseError]:
    """Build a Project; fails with `invalid-record` naming the fields that are missing or malformed."""
    fields = RecordFields(document)
    values = fields.frontmatter_values()
    milestone_ids = tuple(
        s.heading.ref
        for s in document.sections
        if s.heading.level == 2 and s.heading.ref and _MILESTONE_HEADING.match(s.heading.title)
    )
    return RecordFields.validate(
        _PROJECT,
        {
            "id": values.get("id"),
            "type": values.get("type"),
            "title": values.get("title"),
            "description": values.get("description", _description(document)),
            "directory_date": values.get("directory_date", _directory_date(location.path)),
            "owner": values.get("owner", location.inherited_owner),
            "assignee": values.get("assignee"),
            "state": values.get("project-state"),
            "created_at": values.get("created_at"),
            "updated_at": values.get("updated_at"),
            "started_at": values.get("started_at"),
            "resolved_at": values.get("resolved_at"),
            "target_date": values.get("target_date"),
            "tags": values.get("tags", ()),
            "path": location.path,
            "milestone_ids": milestone_ids,
            "blocker_ids": fields.section_refs("Blockers"),
            "source": location.source,
        },
    )
