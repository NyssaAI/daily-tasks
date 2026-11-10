"""Responsibility: Assemble host plugin manifests and distribution bundles from canonical skills and Python sources.
Public interface:
+-- ROOT
+-- assemble(argv)
+-- build_packages()
+-- digest(files)
`-- tree(directory, prefix, exclude_private)
"""

from __future__ import annotations

import hashlib
import json
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
_EXCLUDED_DIRS = frozenset({".nyssa-ai", ".temp", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
_EXCLUDED_PRIVATE_FILES = frozenset({"CODE_MAP.md"})


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
    """Build host manifest files and artifact bundle file maps from canonical source."""
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
    manifests: dict[str, str] = {
        ".claude-plugin/plugin.json": _encode_json(host),
        ".cursor-plugin/plugin.json": _encode_json(host),
        ".codex-plugin/plugin.json": _encode_json(codex_manifest),
    }

    portable_mcp = _encode_json(
        {
            "mcpServers": {
                "daily-tasks": {
                    "command": "uv",
                    "args": ["run", "daily-tasks-mcp"],
                }
            }
        }
    )
    antigravity_mcp = _encode_json(
        {
            "mcpServers": {
                "daily-tasks": {
                    "command": "uv",
                    "args": ["run", "daily-tasks-mcp"],
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
    portable = {**shared, ".mcp.json": claude_mcp, "mcp.json": portable_mcp, **manifests}
    antigravity = {
        **shared,
        "plugin.json": _encode_json({"name": identity["name"], "description": identity["description"]}),
        "mcp_config.json": antigravity_mcp,
    }
    cowork = {**shared, ".mcp.json": claude_mcp, **manifests}
    hermes = {k: v for k, v in shared.items() if k != "plugin.json"}
    hermes["mcp.json"] = portable_mcp
    hermes["plugin.yaml"] = (
        f'name: daily-tasks\nversion: "{identity["version"]}"\n'
        f"description: {json.dumps(identity['description'])}\n"
    )
    hermes["__init__.py"] = (ROOT / "adapters" / "hermes" / "__init__.py").read_text(encoding="utf-8").replace(
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


def _assert_safe_ancestors(destination: Path) -> None:
    current = destination
    while current != ROOT:
        if current.exists() and current.is_symlink():
            raise RuntimeError(f"Unsafe generated path: {current}")
        current = current.parent


def assemble(argv: list[str] | None = None) -> int:
    """Write or check assembled host manifests and artifact packages."""
    args = argv if argv is not None else sys.argv[1:]
    mode = args[0] if args else ""
    if mode not in {"write", "check"}:
        print("Use assemble.py write|check", file=sys.stderr)
        return 1

    manifests, packages = build_packages()
    outputs: dict[str, str] = dict(manifests)
    for fmt, files in packages.items():
        for key, value in files.items():
            outputs[f"artifacts/{fmt}/{key}"] = value

    mismatches: list[str] = []
    for relative, content in outputs.items():
        destination = ROOT / relative
        _assert_safe_ancestors(destination)
        if mode == "write":
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(content, encoding="utf-8", newline="\n")
        else:
            if not destination.is_file():
                mismatches.append(relative)
            else:
                actual_text = destination.read_text(encoding="utf-8").replace("\r\n", "\n")
                if actual_text != content.replace("\r\n", "\n"):
                    mismatches.append(relative)

    artifacts_root = ROOT / "artifacts"
    if artifacts_root.exists():
        for child in sorted(artifacts_root.iterdir(), key=lambda p: p.name):
            if child.name not in packages:
                if mode == "write":
                    if child.is_dir():
                        shutil.rmtree(child)
                    else:
                        child.unlink()
                else:
                    mismatches.append(f"Unexpected artifact bundle: {child.name}")

    for fmt, files in packages.items():
        bundle_dir = artifacts_root / fmt
        actual = tree(bundle_dir)
        for name in actual:
            if name not in files:
                if mode == "write":
                    stale = bundle_dir / name
                    if stale.exists():
                        stale.unlink()
                else:
                    mismatches.append(f"Unexpected artifact: {fmt}/{name}")
        if mode == "write" and bundle_dir.exists():
            for dirpath in sorted((p for p in bundle_dir.rglob("*") if p.is_dir()), reverse=True):
                if not any(dirpath.iterdir()):
                    dirpath.rmdir()

    if mismatches:
        print("\n".join(mismatches), file=sys.stderr)
        return 1

    print(f"{mode}: {len(outputs)} generated files match canonical source")
    return 0


if __name__ == "__main__":
    raise SystemExit(assemble())
