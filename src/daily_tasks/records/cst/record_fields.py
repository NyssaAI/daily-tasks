"""Responsibility: Read the record values that several record parsers derive from a parsed document.
Public interface:
+-- RecordFields
|   +-- definition_of_done()
|   +-- document
|   +-- frontmatter_values()
|   +-- number_from(path, prefix)
|   +-- section(title)
|   +-- section_refs(title)
|   +-- section_text(title)
|   `-- validate(adapter, values)
`-- WORK_MARKS

Section and frontmatter accessors used to map a `MarkdownDocument` onto a domain DTO.
"""

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from nyssa_ai_result import Result, fail_error, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.records.cst.markdown_document import MarkdownDocument
from daily_tasks.records.cst.parse_error import ParseError
from daily_tasks.records.cst.scalar_value import ScalarValue
from daily_tasks.records.cst.section import Section
from daily_tasks.records.cst.split_table_cells import extract_refs, strip_comments

WORK_MARKS: Final[Mapping[str, str]] = {
    " ": "not-started",
    ">": "in-progress",
    "x": "completed",
    "-": "cancelled",
}


@dataclass(frozen=True, slots=True)
class RecordFields:
    """Read-only view over one parsed record document."""

    document: MarkdownDocument

    def definition_of_done(self) -> tuple[dict[str, object], ...]:
        """Checklist items of `## Definition of Done` as DodItem values; done means marked `[x]`."""
        section = self.section("Definition of Done")
        if section is None:
            return ()
        return tuple({"id": i.item_id, "text": i.text, "done": i.mark == "x"} for i in section.checklist_items)

    def frontmatter_values(self) -> dict[str, ScalarValue]:
        """Frontmatter as a key to value mapping; empty when the record has none."""
        frontmatter = self.document.frontmatter
        return {} if frontmatter is None else {field.key: field.value for field in frontmatter.fields}

    def section(self, title: str) -> Section | None:
        """First section whose heading title equals `title`, ignoring case."""
        wanted = title.casefold()
        return next((s for s in self.document.sections if s.heading.title.casefold() == wanted), None)

    def section_refs(self, title: str) -> tuple[str, ...]:
        """Every `<!-- ref: ... -->` id in the section body, in order."""
        section = self.section(title)
        if section is None:
            return ()
        lines = self.document.lines[section.heading.line_index + 1 : section.end_index]
        return tuple(ref for line in lines for ref in extract_refs(line.text))

    def section_text(self, title: str) -> str | None:
        """Section body with comments, list bullets and blank lines removed, joined by spaces."""
        section = self.section(title)
        if section is None:
            return None
        lines = self.document.lines[section.heading.line_index + 1 : section.end_index]
        parts = [strip_comments(line.text).removeprefix("- ").strip() for line in lines]
        return " ".join(part for part in parts if part)

    @staticmethod
    def number_from(path: str, prefix: str) -> int | None:
        """Record number from a file name such as `t3-name.md` (prefix `t`)."""
        name = path.replace("\\", "/").rsplit("/", 1)[-1]
        match = re.match(rf"^{prefix}(\d+)-", name, re.IGNORECASE)
        return int(match.group(1)) if match else None

    @staticmethod
    def validate[T](adapter: TypeAdapter[T], values: Mapping[str, object]) -> Result[T, ParseError]:
        """Validate collected values into a DTO, reporting the failing fields as `invalid-record`."""
        try:
            return ok(adapter.validate_python(dict(values)))
        except ValidationError as error:
            fields = ", ".join(".".join(str(part) for part in issue["loc"]) for issue in error.errors())
            return fail_error(ParseError("invalid-record", f"record does not match its schema: {fields}"))
