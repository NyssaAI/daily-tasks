"""Responsibility: Rebuild a concrete syntax tree after a surgical edit changed its source lines.
Public interface:
`-- reparse_lines(lines)

Shared final step of every surgical mutation: parse the edited lines again.
"""

from collections.abc import Sequence

from nyssa_ai_result import Result

from daily_tasks.storage.cst.markdown_document import MarkdownDocument
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.parse_markdown import parse_markdown
from daily_tasks.storage.cst.source_line import SourceLine
from daily_tasks.storage.cst.write_markdown import write_markdown


def reparse_lines(lines: Sequence[SourceLine]) -> Result[MarkdownDocument, ParseError]:
    """Parse the text the edited `lines` spell, so node positions match the new source."""
    return parse_markdown(write_markdown(MarkdownDocument(tuple(lines), None, (), (), ())))
