# Responsibility: Hold one scalar YAML frontmatter field and its source position.
# Public interface:
# `-- FrontmatterField
#     +-- key
#     +-- line_index
#     +-- raw_value
#     +-- value
#     `-- value_column
"""Frontmatter field node: the position lets edits replace only the value characters."""

from dataclasses import dataclass

from daily_tasks.storage.cst.scalar_value import ScalarValue


@dataclass(frozen=True, slots=True)
class FrontmatterField:
    """Scalar YAML field; `value_column` is where `raw_value` starts on its line."""

    key: str
    raw_value: str
    value: ScalarValue
    line_index: int
    value_column: int
