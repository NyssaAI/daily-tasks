"""Responsibility: Validate canonical skills, relative links, path hygiene, harness adapters, and version parity.
Public interface:
+-- validate()
`-- validate_repository(root)
"""

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


def validate_repository(root: Path = ROOT) -> list[str]:
    """Validate skill frontmatter, relative Markdown links, path hygiene, harness adapters, and version parity."""
    files = tree(root / "skills", "skills/")
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
            target = (root / Path(name).parent / target_part).resolve()
            if not target.is_relative_to(root):
                errors.append(f"Escaping link: {name}")
                continue
            if not target.exists():
                errors.append(f"Broken link in {name}: {raw_target}")

        if _LEAK_RE.search(content):
            errors.append(f"Local path leaked: {name}")

    identity = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    if identity.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("Missing or unsupported Agent Plugins v1 $schema in plugin.json")
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject.get("project", {}).get("version")
    if identity.get("version") != pyproject_version or len(names) != 1:
        errors.append("Version or skill inventory mismatch")

    readme_path = root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        version_match = re.search(r"Version\s+\*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*", readme_text)
        if version_match is None or version_match.group(1) != identity.get("version"):
            errors.append("README.md version mismatch")

    hermes_adapter = root / "harness-adapters" / "hermes" / "__init__.py"
    if not hermes_adapter.is_file():
        errors.append("Missing harness-adapters/hermes/__init__.py")
    if (root / "adapters").exists():
        errors.append("Retired adapters/ directory must not exist; use harness-adapters/")
    if (root / "artifacts").exists():
        errors.append("Retired artifacts/ directory must not exist; stage bundles into .temp/dist/")

    mcp_path = root / ".mcp.json"
    if not mcp_path.exists():
        errors.append("Missing .mcp.json manifest")
    else:
        try:
            mcp_raw = mcp_path.read_text(encoding="utf-8")
            if "${PLUGIN_DATA}" in mcp_raw:
                errors.append("Retired ${PLUGIN_DATA} placeholder must not appear in .mcp.json")
            mcp_data = json.loads(mcp_raw)
            servers = mcp_data.get("mcpServers") if isinstance(mcp_data, dict) else None
            server_cfg = servers.get("daily-tasks") if isinstance(servers, dict) else None
            if (
                not isinstance(server_cfg, dict)
                or not isinstance(server_cfg.get("command"), str)
                or not server_cfg["command"].strip()
                or not isinstance(server_cfg.get("args"), list)
                or not server_cfg["args"]
            ):
                errors.append("Malformed .mcp.json: daily-tasks server requires command and non-empty args")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid .mcp.json: {exc}")

    portable_mcp_path = root / "mcp.json"
    if not portable_mcp_path.exists():
        errors.append("Missing mcp.json portable manifest")
    else:
        try:
            portable_raw = portable_mcp_path.read_text(encoding="utf-8")
            if "${PLUGIN_DATA}" in portable_raw:
                errors.append("Retired ${PLUGIN_DATA} placeholder must not appear in mcp.json")
            portable_mcp_data = json.loads(portable_raw)
            portable_servers = portable_mcp_data.get("mcpServers") if isinstance(portable_mcp_data, dict) else None
            portable_server_cfg = portable_servers.get("daily-tasks") if isinstance(portable_servers, dict) else None
            if (
                not isinstance(portable_mcp_data, dict)
                or set(portable_mcp_data) != {"$schema", "mcpServers"}
                or portable_mcp_data.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"
                or not isinstance(portable_server_cfg, dict)
                or portable_server_cfg.get("type") != "stdio"
                or not isinstance(portable_server_cfg.get("command"), str)
                or not portable_server_cfg["command"].strip()
                or not isinstance(portable_server_cfg.get("args"), list)
                or not portable_server_cfg["args"]
            ):
                errors.append("Malformed mcp.json: requires Agent Plugins v1 $schema and stdio daily-tasks server")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid mcp.json: {exc}")

    return errors


def validate() -> int:
    """Run repository validation checks and report results."""
    errors = validate_repository()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print("Validated 1 skill, workflows, relative links, path hygiene, harness adapters, and version parity")
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
