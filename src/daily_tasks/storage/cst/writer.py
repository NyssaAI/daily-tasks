# Responsibility: Serialize a concrete syntax tree back to Markdown text byte for byte.
# Public interface:
# +-- line_ending(document)
# `-- write_markdown(document)
"""Writer: joins the stored lines with their own terminators, so unedited records stay byte-identical."""

from daily_tasks.storage.cst.nodes import MarkdownDocument


def write_markdown(document: MarkdownDocument) -> str:
    """Return the document text; `write_markdown(parse_markdown(t).value) == t` for every input `t`."""
    return "".join(line.text + line.ending for line in document.lines)


def line_ending(document: MarkdownDocument) -> str:
    """Terminator to use for inserted lines: the first one the document uses, else `\\n`."""
    return next((line.ending for line in document.lines if line.ending), "\n")
