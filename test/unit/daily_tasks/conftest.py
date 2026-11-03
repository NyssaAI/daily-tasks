# Responsibility: Locate the canonical spec examples for the test suite.
# Public interface:
# +-- SPECS_ROOT
# `-- load_spec(name)
"""Shared test helpers for reading `docs/specs/*.json`."""

import json
from pathlib import Path
from typing import Final

from pydantic import JsonValue, TypeAdapter

SPECS_ROOT: Final[Path] = Path(__file__).resolve().parents[3] / "docs" / "specs"
_JSON: Final[TypeAdapter[JsonValue]] = TypeAdapter(JsonValue)


def load_spec(name: str) -> JsonValue:
    """Parse one spec example as plain JSON."""
    return _JSON.validate_python(json.loads((SPECS_ROOT / name).read_text(encoding="utf-8")))
