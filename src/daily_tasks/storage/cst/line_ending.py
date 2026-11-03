# Responsibility: Choose the line terminator for lines inserted into a Markdown record.
# Public interface:
# `-- line_ending(document)
"""Inserted lines reuse the record's own terminator so edits do not mix line endings."""

from daily_tasks.storage.cst.markdown_document import MarkdownDocument


def line_ending(document: MarkdownDocument) -> str:
    """Terminator to use for inserted lines: the first one the document uses, else `\\n`."""
    return next((line.ending for line in document.lines if line.ending), "\n")
