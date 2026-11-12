"""Responsibility: Read and format scalar YAML frontmatter values.
Public interface:
+-- format_scalar(value, quoted)
`-- parse_frontmatter(lines)

Scalar-only YAML subset: quoted or bare strings, integers, booleans, null and flow lists of strings.
"""

import json
import re
from typing import Final

from nyssa_ai_result import Result, fail_error, ok

from daily_tasks.storage.cst.frontmatter import Frontmatter
from daily_tasks.storage.cst.frontmatter_field import FrontmatterField
from daily_tasks.storage.cst.parse_error import ParseError
from daily_tasks.storage.cst.scalar_value import ScalarValue
from daily_tasks.storage.cst.source_line import SourceLine

_DELIMITER: Final = "---"
_FIELD: Final = re.compile(r"^([A-Za-z_][\w-]*):[ \t]*")
_INT: Final = re.compile(r"^-?\d+$")


def _parse_string(raw: str) -> str | None:
    if raw.startswith('"'):
        try:
            decoded = json.loads(raw)
        except json.JSONDecodeError:
            return None
        return decoded if isinstance(decoded, str) else None
    if raw.startswith("'"):
        return raw[1:-1].replace("''", "'") if len(raw) >= 2 and raw.endswith("'") else None
    return raw


def _parse_list(raw: str) -> tuple[str, ...] | None:
    inner = raw[1:-1].strip()
    if not inner:
        return ()
    items: list[str] = []
    for part in inner.split(","):
        item = _parse_string(part.strip())
        if item is None:
            return None
        items.append(item)
    return tuple(items)


def _parse_value(raw: str) -> ScalarValue | ParseError:
    if raw in ("", "null", "~"):
        return None
    if raw in ("true", "false"):
        return raw == "true"
    if _INT.match(raw):
        return int(raw)
    if raw.startswith("[") and raw.endswith("]"):
        items = _parse_list(raw)
        return items if items is not None else ParseError("invalid-list", f"unsupported list value {raw!r}")
    value = _parse_string(raw)
    return value if value is not None else ParseError("invalid-string", f"unterminated string {raw!r}")


def _strip_trailing_comment(raw: str) -> str:
    if raw.startswith(("'", '"', "[")):
        return raw.rstrip()
    return raw.split(" #", 1)[0].rstrip()


def parse_frontmatter(lines: tuple[SourceLine, ...]) -> Result[Frontmatter | None, ParseError]:
    """Parse the leading `---` block; a document without one has no frontmatter.

    Fails with `unclosed-frontmatter`, `non-scalar-field`, `duplicate-field` or a value code.
    """
    if not lines or lines[0].text.lstrip("\ufeff") != _DELIMITER:
        return ok(None)
    fields: list[FrontmatterField] = []
    for index in range(1, len(lines)):
        text = lines[index].text
        if text == _DELIMITER:
            return ok(Frontmatter(fields=tuple(fields), open_index=0, close_index=index))
        if not text.strip() or text.lstrip().startswith("#"):
            continue
        match = _FIELD.match(text)
        if match is None:
            return fail_error(ParseError("non-scalar-field", f"unsupported frontmatter line {text!r}", index + 1))
        key = match.group(1)
        if any(field.key == key for field in fields):
            return fail_error(ParseError("duplicate-field", f"frontmatter key {key!r} repeats", index + 1))
        raw = _strip_trailing_comment(text[match.end() :])
        value = _parse_value(raw)
        if isinstance(value, ParseError):
            return fail_error(ParseError(value.code, value.detail, index + 1))
        fields.append(FrontmatterField(key, raw, value, index, match.end()))
    return fail_error(ParseError("unclosed-frontmatter", "frontmatter has no closing '---'", 1))


def format_scalar(value: ScalarValue, quoted: bool) -> str:
    """Format a value as YAML; strings are double-quoted when `quoted` or when bare text would be ambiguous."""
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, tuple):
        return "[" + ", ".join(json.dumps(item, ensure_ascii=False) for item in value) + "]"
    is_ambiguous = isinstance(_parse_value(value), (int, bool)) or value in ("", "null", "~")
    is_unsafe = value != value.strip() or value.startswith(("'", '"', "[")) or " #" in value or ": " in value
    if quoted or is_ambiguous or is_unsafe:
        return json.dumps(value, ensure_ascii=False)
    return value
