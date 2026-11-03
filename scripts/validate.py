# Responsibility: Validate canonical skills, relative links, path hygiene, and version parity across plugin.json and pyproject.toml.
# Public interface:
# +-- validate()
# `-- validate_repository()

from __future__ import annotations

import json
import re
import sys
import tomllib
from pathlib import Path

from assemble import ROOT, tree

_FRONTMATTER_RE = re.compile(r"^---\nname: ([a-z0-9-]+)\ndescription: ([^\n]+)\n---")
_LINK_RE = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_LEAK_RE = re.compile(r"C:[\\/]|D:[\\/]|\.codex/plugins/cache")


def validate_repository() -> list[str]:
    """Validate skill frontmatter, relative Markdown links, path hygiene, and version parity."""
    files = tree(ROOT / "skills", "skills/")
    errors: list[str] = []
    names: set[str] = set()

    for name, content in files.items():
        if name.endswith("/SKILL.md"):
            match = _FRONTMATTER_RE.match(content)
            expected_dir = Path(name).parent.name
            if match is None or match.group(1) != expected_dir or match.group(1) in names:
                errors.append(f"Invalid skill frontmatter: {name}")
            else:
                names.add(match.group(1))

        for match in _LINK_RE.finditer(content):
            raw_target = match.group(1)
            if raw_target.startswith(("http://", "https://", "#")):
                continue
            target_part = raw_target.split("#", 1)[0]
            target = (ROOT / Path(name).parent / target_part).resolve()
            if not target.is_relative_to(ROOT):
                errors.append(f"Escaping link: {name}")
                continue
            if not target.exists():
                errors.append(f"Broken link in {name}: {raw_target}")

        if _LEAK_RE.search(content):
            errors.append(f"Local path leaked: {name}")

    identity = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject.get("project", {}).get("version")
    if identity.get("version") != pyproject_version or len(names) != 6:
        errors.append("Version or skill inventory mismatch")

    return errors


def validate() -> int:
    """Run repository validation checks and report results."""
    errors = validate_repository()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Validated 6 skills, relative links, path hygiene, and plugin/pyproject version parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
