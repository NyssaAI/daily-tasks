"""Responsibility: Serialize a concrete syntax tree back to Markdown text byte for byte.
Public interface:
`-- write_markdown(document)

Writer: joins the stored lines with their own terminators, so unedited records stay byte-identical.
"""

from daily_tasks.records.cst.markdown_document import MarkdownDocument


def write_markdown(document: MarkdownDocument) -> str:
    """Return the document text; `write_markdown(parse_markdown(t).value) == t` for every input `t`."""
    return "".join(line.text + line.ending for line in document.lines)
