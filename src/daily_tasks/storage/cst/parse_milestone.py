# Responsibility: Map a parsed milestone Markdown record onto the Milestone DTO.
# Public interface:
# `-- parse_milestone(document, location)
"""Milestone parser: frontmatter, Definition of Done, task table and blocker table."""

import re
from typing import Final

from nyssa_ai_result import Result
from pydantic import TypeAdapter

from daily_tasks.domain import Milestone
from daily_tasks.storage.cst.nodes import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.record_fields import RecordFields
from daily_tasks.storage.cst.types import RecordLocation

_MILESTONE: Final[TypeAdapter[Milestone]] = TypeAdapter(Milestone)
_TITLE_NUMBER: Final = re.compile(r"^(?:\[.\]\s+)?M(\d+):")


def _number(document: MarkdownDocument, path: str) -> int | None:
    title = next((s.heading.title for s in document.sections if s.heading.level == 1), "")
    match = _TITLE_NUMBER.match(title)
    return int(match.group(1)) if match else RecordFields.number_from(path, "m")


def parse_milestone(document: MarkdownDocument, location: RecordLocation) -> Result[Milestone, ParseError]:
    """Build a Milestone; fails with `invalid-record` naming the fields that are missing or malformed."""
    fields = RecordFields(document)
    values = fields.frontmatter_values()
    return RecordFields.validate(
        _MILESTONE,
        {
            "id": values.get("id"),
            "type": values.get("type"),
            "record_version": values.get("record_version"),
            "project_id": values.get("project_id"),
            "number": values.get("number", _number(document, location.path)),
            "title": values.get("title"),
            "owner": values.get("owner", location.inherited_owner),
            "assignee": values.get("assignee"),
            "state": values.get("milestone-state"),
            "created_at": values.get("created_at"),
            "updated_at": values.get("updated_at"),
            "started_at": values.get("started_at"),
            "resolved_at": values.get("resolved_at"),
            "target_date": values.get("target_date"),
            "tags": values.get("tags", ()),
            "path": location.path,
            "definition_of_done": fields.definition_of_done(),
            "task_ids": fields.section_refs("Tasks"),
            "blocked_by": fields.section_refs("Blockers"),
            "source": location.source,
        },
    )
