# Responsibility: Name the scalar YAML values a frontmatter field can hold.
# Public interface:
# `-- ScalarValue
"""Scalar YAML subset: strings, integers, booleans, null and flow lists of strings."""

type ScalarValue = str | int | bool | None | tuple[str, ...]
