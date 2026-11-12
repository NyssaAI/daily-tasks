"""Responsibility: Map a parsed task Markdown record onto a Task entity.
Public interface:
`-- parse_task(document, location)
"""

import re
from typing import Final

from nyssa_ai_result import Result
from pydantic import TypeAdapter

from daily_tasks.core.records.task import Task
from daily_tasks.core.records.types import RecordLocation
from daily_tasks.records.cst.markdown_document import MarkdownDocument
from daily_tasks.records.cst.parse_error import ParseError
from daily_tasks.records.cst.record_fields import RecordFields
from daily_tasks.records.cst.split_table_cells import extract_id

_TASK: Final[TypeAdapter[Task]] = TypeAdapter(Task)
_TITLE_TASK_NUMBER: Final = re.compile(r"\b(?:M\d+-)?T(\d+)\b", re.IGNORECASE)


def _task_number(document: MarkdownDocument, path: str) -> int:
    from_file = RecordFields.number_from(path, "t")
    if from_file is not None:
        return from_file
    title = next((s.heading.title for s in document.sections if s.heading.level == 1), "")
    match = _TITLE_TASK_NUMBER.search(title)
    if match:
        return int(match.group(1))
    return 1


def parse_task(document: MarkdownDocument, location: RecordLocation) -> Result[Task, ParseError]:
    """Build a Task; fails with `invalid-record` naming the fields that are missing or malformed."""
    fields = RecordFields(document)
    values = fields.frontmatter_values()
    task_id = values.get("id")
    if task_id is None:
        task_id = next((extract_id(line.text) for line in document.lines if extract_id(line.text)), None)
    title = values.get("title")
    if not title:
        title = next((s.heading.title for s in document.sections if s.heading.level == 1), None)
    state = values.get("state") or values.get("task-state")
    if state == "done":
        state = "completed"
    return RecordFields.validate(
        _TASK,
        {
            "id": task_id,
            "type": values.get("type"),
            "record_version": values.get("record_version") or 1,
            "project_id": values.get("project_id"),
            "milestone_id": values.get("milestone_id"),
            "number": values.get("number") or _task_number(document, location.path),
            "title": title,
            "owner": values.get("owner", location.inherited_owner),
            "assignee": values.get("assignee"),
            "state": state,
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
