# Responsibility: Map a parsed task Markdown record onto the Task DTO.
# Public interface:
# `-- parse_task(document, location)
"""Task record parser: frontmatter, Definition of Done and relation sections."""

from typing import Final

from nyssa_ai_result import Result
from pydantic import TypeAdapter

from daily_tasks.domain import Task
from daily_tasks.storage.cst.nodes import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.record_fields import RecordFields
from daily_tasks.storage.cst.types import RecordLocation

_TASK: Final[TypeAdapter[Task]] = TypeAdapter(Task)


def parse_task(document: MarkdownDocument, location: RecordLocation) -> Result[Task, ParseError]:
    """Build a Task; fails with `invalid-record` naming the fields that are missing or malformed."""
    fields = RecordFields(document)
    values = fields.frontmatter_values()
    return RecordFields.validate(
        _TASK,
        {
            "id": values.get("id"),
            "type": values.get("type"),
            "record_version": values.get("record_version"),
            "project_id": values.get("project_id"),
            "milestone_id": values.get("milestone_id"),
            "number": values.get("number", RecordFields.number_from(location.path, "t")),
            "title": values.get("title"),
            "owner": values.get("owner", location.inherited_owner),
            "assignee": values.get("assignee"),
            "state": values.get("task-state"),
            "created_at": values.get("created_at"),
            "updated_at": values.get("updated_at"),
            "started_at": values.get("started_at"),
            "resolved_at": values.get("resolved_at"),
            "target_date": values.get("target_date"),
            "tags": values.get("tags", ()),
            "path": location.path,
            "definition_of_done": fields.definition_of_done(),
            "depends_on": fields.section_refs("Depends on"),
            "required_by": fields.section_refs("Required by"),
            "blocked_by": fields.section_refs("Blocked by"),
            "source": location.source,
        },
    )
