"""Responsibility: Assemble harness-adapter manifests and stage distribution bundles into .temp/dist/.
Public interface:
+-- DEFAULT_DIST_DIR
+-- ROOT
+-- assemble(argv)
+-- build_packages()
+-- digest(files)
`-- tree(directory, prefix, exclude_private)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_DIST_DIR = ROOT / ".temp" / "dist"
_EXCLUDED_DIRS = frozenset({".nyssa-ai", ".temp", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
_EXCLUDED_PRIVATE_FILES = frozenset({"CODE_MAP.md"})
_MCP_SCHEMA_V1 = "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json"


def _encode_json(value: object) -> str:
    return json.dumps(value, indent=2) + "\n"


def tree(directory: Path, prefix: str = "", exclude_private: bool = False) -> dict[str, str]:
    """Read a directory tree into a normalized relative-path -> UTF-8 LF text mapping."""
    files: dict[str, str] = {}
    if not directory.exists():
        return files
    for item in sorted(directory.iterdir(), key=lambda p: p.name):
        if item.name in {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}:
            continue
        if exclude_private and (item.name in _EXCLUDED_DIRS or item.name in _EXCLUDED_PRIVATE_FILES):
            continue
        name = f"{prefix}{item.name}"
        if item.is_symlink():
            raise RuntimeError(f"Symlink cannot be packaged: {name}")
        if item.is_dir():
            files.update(tree(item, f"{name}/", exclude_private))
        else:
            files[name] = item.read_text(encoding="utf-8").replace("\r\n", "\n")
    return files


def digest(files: dict[str, str]) -> str:
    """Compute a deterministic SHA-256 digest over a sorted file mapping."""
    hasher = hashlib.sha256()
    for name, value in sorted(files.items()):
        hasher.update(f"{name}\0{value}\0".encode())
    return hasher.hexdigest()


def build_packages() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    """Build root harness-adapter manifests and distribution bundle file maps from canonical source."""
    identity = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    host = {k: v for k, v in identity.items() if k != "$schema"}
    codex_manifest = {
        **host,
        "skills": "./skills/",
        "interface": {
            "displayName": "Daily Tasks",
            "shortDescription": "Personal tasks and daily planning",
            "developerName": "NyssaAI",
            "category": "Productivity",
        },
    }
    host_manifests: dict[str, str] = {
        ".claude-plugin/plugin.json": _encode_json(host),
        ".cursor-plugin/plugin.json": _encode_json(host),
        ".codex-plugin/plugin.json": _encode_json(codex_manifest),
    }

    portable_mcp = _encode_json(
        {
            "$schema": _MCP_SCHEMA_V1,
            "mcpServers": {
                "daily-tasks": {
                    "type": "stdio",
                    "command": "python3",
                    "args": ["${PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py"],
                }
            },
        }
    )
    manifests: dict[str, str] = {
        **host_manifests,
        "mcp.json": portable_mcp,
    }
    antigravity_mcp = _encode_json(
        {
            "mcpServers": {
                "daily-tasks": {
                    "command": "python3",
                    "args": ["./src/daily_tasks/launch_mcp.py"],
                    "disabled": False,
                }
            }
        }
    )

    shared: dict[str, str] = {
        "plugin.json": _encode_json(identity),
        "LICENSE": (ROOT / "LICENSE").read_text(encoding="utf-8").replace("\r\n", "\n"),
        "pyproject.toml": (ROOT / "pyproject.toml").read_text(encoding="utf-8").replace("\r\n", "\n"),
    }
    for folder in ("skills", "src"):
        shared.update(tree(ROOT / folder, f"{folder}/", exclude_private=True))

    claude_mcp = (ROOT / ".mcp.json").read_text(encoding="utf-8").replace("\r\n", "\n")
    portable = {**shared, ".mcp.json": claude_mcp, **manifests}
    antigravity = {
        **shared,
        "plugin.json": _encode_json({"name": identity["name"], "description": identity["description"]}),
        "mcp_config.json": antigravity_mcp,
    }
    cowork = {**shared, ".mcp.json": claude_mcp, **host_manifests}
    hermes = {k: v for k, v in shared.items() if k != "plugin.json"}
    hermes["mcp.json"] = portable_mcp
    hermes["plugin.yaml"] = (
        f'name: daily-tasks\nversion: "{identity["version"]}"\n'
        f"description: {json.dumps(identity['description'])}\n"
    )
    hermes["__init__.py"] = (ROOT / "harness-adapters" / "hermes" / "__init__.py").read_text(encoding="utf-8").replace(
        "\r\n", "\n"
    )

    packages: dict[str, dict[str, str]] = {
        "portable": portable,
        "antigravity": antigravity,
        "cowork": cowork,
        "hermes": hermes,
    }
    for fmt, files in packages.items():
        files["assembly.json"] = _encode_json(
            {
                "format": fmt,
                "version": identity["version"],
                "source_sha256": digest(files),
            }
        )
    return manifests, packages


def _assert_safe_ancestors(destination: Path, boundary: Path) -> None:
    current = destination
    while current != boundary and current != current.parent:
        if current.exists() and current.is_symlink():
            raise RuntimeError(f"Unsafe generated path: {current}")
        current = current.parent


def _parse_args(argv: list[str] | None) -> tuple[str, Path] | None:
    parser = argparse.ArgumentParser(prog="assemble.py", add_help=False)
    parser.add_argument("mode", nargs="?", default="write")
    parser.add_argument("--output-dir", default=str(DEFAULT_DIST_DIR))
    parsed, unknown = parser.parse_known_args(argv if argv is not None else sys.argv[1:])
    if unknown or parsed.mode not in {"write", "check"}:
        return None
    return str(parsed.mode), Path(parsed.output_dir).expanduser().resolve()


def assemble(argv: list[str] | None = None) -> int:
    """Write or check assembled harness-adapter manifests and staged bundles in `.temp/dist/`."""
    parsed = _parse_args(argv)
    if parsed is None:
        print("Use assemble.py [write|check] [--output-dir DIR]", file=sys.stderr)
        return 1
    mode, dist_root = parsed

    manifests, packages = build_packages()
    mismatches: list[str] = []

    for relative, content in manifests.items():
        destination = ROOT / relative
        _assert_safe_ancestors(destination, ROOT)
        if mode == "write":
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="\n")
        elif not destination.is_file() or destination.read_text(encoding="utf-8").replace("\r\n", "\n") != content:
            mismatches.append(relative)

    bundle_count = 0
    for fmt, files in packages.items():
        for key, value in files.items():
            bundle_count += 1
            destination = dist_root / fmt / key
            _assert_safe_ancestors(destination, dist_root.parent)
            if mode == "write":
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(value, encoding="utf-8", newline="\n")
            elif not destination.is_file() or destination.read_text(encoding="utf-8").replace("\r\n", "\n") != value:
                mismatches.append(f"{dist_root.as_posix()}/{fmt}/{key}")

    if dist_root.exists():
        for child in sorted(dist_root.iterdir(), key=lambda p: p.name):
            if child.name not in packages:
                if mode == "write":
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                else:
                    mismatches.append(f"Unexpected dist bundle: {child.name}")

    for fmt, files in packages.items():
        bundle_dir = dist_root / fmt
        actual = tree(bundle_dir)
        for name in actual:
            if name not in files:
                if mode == "write":
                    stale = bundle_dir / name
                    if stale.exists():
                        stale.unlink()
                else:
                    mismatches.append(f"Unexpected bundle file: {fmt}/{name}")
        if mode == "write" and bundle_dir.exists():
            for dirpath in sorted((p for p in bundle_dir.rglob("*") if p.is_dir()), reverse=True):
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()

    if mismatches:
        print("\n".join(mismatches), file=sys.stderr)
        return 1

    total = len(manifests) + bundle_count
    print(f"{mode}: {total} generated files match canonical source (dist: {dist_root.as_posix()})")
    return 0


if __name__ == "__main__":
    raise SystemExit(assemble())
