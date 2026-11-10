"""Responsibility: Register bundled Daily Tasks skills with the Hermes Agent plugin runtime.
Public interface:
`-- register(ctx)

Hermes Agent runtime registration shim copied into `artifacts/hermes/__init__.py` by `scripts/assemble.py`.
"""

from pathlib import Path
from typing import Protocol


class _HermesPluginContext(Protocol):
    """Subset of the Hermes plugin registration context used to register skills."""

    def register_skill(self, name: str, path: Path) -> None:
        """Register one skill directory entrypoint with Hermes."""


def register(ctx: _HermesPluginContext) -> None:
    """Register every bundled `skills/*/SKILL.md` entrypoint in deterministic order."""
    for skill in sorted((Path(__file__).resolve().parent / "skills").glob("*/SKILL.md")):
        ctx.register_skill(skill.parent.name, skill)
