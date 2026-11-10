"""Responsibility: Compute the Markdown text of a record after one adjudicated record change.
Public interface:
+-- FRONTMATTER_KEYS
`-- apply_record_change(text, change)

Pure surgical edit: `after` values become frontmatter values and Definition of Done marks.
"""

from collections.abc import Mapping
from typing import Final

from nyssa_ai_result import Ok, Result, fail_error, ok
from pydantic import JsonValue

from daily_tasks.domain import RecordChange
from daily_tasks.storage.cst import (
    MarkdownDocument,
    ParseError,
    ScalarValue,
    parse_markdown,
    set_checklist_mark,
    set_frontmatter_field,
    write_markdown,
)

FRONTMATTER_KEYS: Final[frozenset[str]] = frozenset(
    {"state", "target_date", "assignee", "owner", "impact", "updated_at", "started_at", "resolved_at", "tags"}
)
_DOD: Final = "dod"
_DOD_PREFIX: Final = "dod:"


def _scalar(key: str, value: JsonValue) -> ScalarValue | ParseError:
    if value is None or isinstance(value, (str, int, bool)):
        return value
    if isinstance(value, list) and all(isinstance(item, str) for item in value):
        return tuple(str(item) for item in value)
    return ParseError("unsupported-value", f"field {key!r} needs a scalar or a list of strings")


def _dod_marks(after: Mapping[str, JsonValue]) -> dict[str, bool] | ParseError:
    marks: dict[str, bool] = {}
    nested = after.get(_DOD, {})
    if not isinstance(nested, dict):
        return ParseError("unsupported-value", "field 'dod' needs an item id to boolean mapping")
    flat = {key.removeprefix(_DOD_PREFIX): value for key, value in after.items() if key.startswith(_DOD_PREFIX)}
    for item_id, done in {**nested, **flat}.items():
        if not isinstance(done, bool):
            return ParseError("unsupported-value", f"DoD item {item_id} needs a boolean")
        marks[item_id] = done
    return marks


def _set_fields(
    document: MarkdownDocument, record_type: str, after: Mapping[str, JsonValue]
) -> Result[MarkdownDocument, ParseError]:
    for key, value in after.items():
        if key == _DOD or key.startswith(_DOD_PREFIX):
            continue
        if key not in FRONTMATTER_KEYS:
            return fail_error(ParseError("unsupported-field", f"field {key!r} cannot be changed in place"))
        scalar = _scalar(key, value)
        if isinstance(scalar, ParseError):
            return fail_error(scalar)
        edited = set_frontmatter_field(document, f"{record_type}-state" if key == "state" else key, scalar)
        if not isinstance(edited, Ok):
            return edited
        document = edited.value
    return ok(document)


def apply_record_change(text: str, change: RecordChange) -> Result[str, ParseError]:
    """Return `text` with only the bytes of the changed values replaced; line endings are kept.

    `state` maps to the `<record_type>-state` key; `dod` (id to bool mapping) and `dod:<id>` keys set
    `[x]` or `[ ]`. Fails with `unsupported-change` for creations, deletions and daily-plan records,
    `unsupported-field`, `unsupported-value`, a parse error code, or `item-not-found`.
    """
    after = change.after
    if change.before is None or after is None or change.record_type == "daily-plan":
        return fail_error(ParseError("unsupported-change", "only in-place edits of existing records are supported"))
    parsed = parse_markdown(text)
    if not isinstance(parsed, Ok):
        return parsed
    marks = _dod_marks(after)
    if isinstance(marks, ParseError):
        return fail_error(marks)
    edited = _set_fields(parsed.value, change.record_type, after)
    if not isinstance(edited, Ok):
        return edited
    document = edited.value
    for item_id, done in marks.items():
        marked = set_checklist_mark(document, item_id, "x" if done else " ")
        if not isinstance(marked, Ok):
            return marked
        document = marked.value
    return ok(write_markdown(document))
