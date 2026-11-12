"""Responsibility: Map a parsed blocker Markdown record onto a Blocker entity.
Public interface:
`-- parse_blocker(document, location)
"""

import re
from typing import Final

from nyssa_ai_result import Result
from pydantic import TypeAdapter

from daily_tasks.core.records.blocker import Blocker
from daily_tasks.core.records.types import RecordLocation
from daily_tasks.records.cst.markdown_document import MarkdownDocument
from daily_tasks.records.cst.parse_error import ParseError
from daily_tasks.records.cst.record_fields import RecordFields

_BLOCKER: Final[TypeAdapter[Blocker]] = TypeAdapter(Blocker)
_TITLE_NUMBER: Final = re.compile(r"^B(\d+)\b")


def _number(document: MarkdownDocument, path: str) -> int | None:
    title = next((s.heading.title for s in document.sections if s.heading.level == 1), "")
    match = _TITLE_NUMBER.match(title)
    return int(match.group(1)) if match else RecordFields.number_from(path, "b")


def parse_blocker(document: MarkdownDocument, location: RecordLocation) -> Result[Blocker, ParseError]:
    """Build a Blocker; `impact` prefers the `## Impact & Summary` text over the frontmatter level."""
    fields = RecordFields(document)
    values = fields.frontmatter_values()
    impact = fields.section_text("Impact & Summary") or fields.section_text("Impact") or values.get("impact")
    state = values.get("state") or values.get("blocker-state")
    return RecordFields.validate(
        _BLOCKER,
        {
            "id": values.get("id"),
            "type": values.get("type"),
            "project_id": values.get("project_id"),
            "number": values.get("number", _number(document, location.path)),
            "title": values.get("title"),
            "impact": impact,
            "resolved_when": values.get("resolved_when", fields.section_text("Resolved When")),
            "owner": values.get("owner", location.inherited_owner),
            "state": state,
            "created_at": values.get("created_at"),
            "updated_at": values.get("updated_at"),
            "resolved_at": values.get("resolved_at"),
            "path": location.path,
            "blocks": fields.section_refs("Blocks"),
            "source": location.source,
        },
    )
