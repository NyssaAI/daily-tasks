"""Responsibility: Change or add one frontmatter field without touching unrelated bytes.
Public interface:
`-- set_frontmatter_field(document, key, value)

Surgical mutation: replaces only the value characters, or inserts one whole new field line.
"""

from dataclasses import replace

from nyssa_ai_result import Result, fail_error

from daily_tasks.storage.cst.line_ending import line_ending
from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.parse_frontmatter import format_scalar
from daily_tasks.storage.cst.reparse_lines import reparse_lines
from daily_tasks.storage.cst.scalar_value import ScalarValue
from daily_tasks.storage.cst.source_line import SourceLine


def set_frontmatter_field(
    document: MarkdownDocument, key: str, value: ScalarValue
) -> Result[MarkdownDocument, ParseError]:
    """Replace the value of `key`, keeping its quoting style, or add `key` before the closing `---`.

    Fails with `missing-frontmatter` when the record has no frontmatter block.
    """
    frontmatter = document.frontmatter
    if frontmatter is None:
        return fail_error(ParseError("missing-frontmatter", "record has no frontmatter to update"))
    lines = list(document.lines)
    field = next((f for f in frontmatter.fields if f.key == key), None)
    if field is None:
        new_line = SourceLine(text=f"{key}: {format_scalar(value, quoted=True)}", ending=line_ending(document))
        lines.insert(frontmatter.close_index, new_line)
        return reparse_lines(lines)
    old = lines[field.line_index]
    is_quoted = field.raw_value.startswith('"') or (field.value is None and isinstance(value, str))
    start = field.value_column
    end = start + len(field.raw_value)
    lines[field.line_index] = replace(old, text=old.text[:start] + format_scalar(value, is_quoted) + old.text[end:])
    return reparse_lines(lines)
