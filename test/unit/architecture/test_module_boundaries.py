"""Responsibility: Enforce Scale B SOLID Modular Monolith boundaries, role-named contracts, and naming invariants.
Public interface:
+-- test_no_retired_horizontal_layer_directories()
+-- test_core_is_pure_and_free_of_outer_or_transport_imports()
+-- test_core_subdomains_follow_acyclic_dependency_direction()
+-- test_feature_slices_do_not_cross_import_or_depend_on_hosting_or_transports()
+-- test_transports_do_not_import_feature_slices_or_hosting()
`-- test_no_banned_type_or_port_suffixes_in_src()

AST-based architecture verification (ARCH-BOUNDARY, ARCH-PORTABILITY, ARCH-DATA, ARCH-NAME).
"""

from __future__ import annotations

import ast
import re
from pathlib import Path
from typing import Final

SRC_ROOT: Final = Path(__file__).resolve().parents[3] / "src" / "daily_tasks"

BANNED_DIRS: Final = frozenset(
    {
        "adapters",
        "ports",
        "domain",
        "storage",
        "auth",
        "credentials",
        "graph",
        "matching",
        "server",
        "session",
        "contracts",
        "shared",
        "utils",
        "helpers",
        "common",
        "misc",
        "types",
        "models",
    },
)

CORE_FORBIDDEN_EXTERNAL_ROOTS: Final = frozenset(
    {
        "os",
        "pathlib",
        "shutil",
        "subprocess",
        "socket",
        "http",
        "mcp",
        "fastmcp",
        "httpx",
        "requests",
        "aiohttp",
        "nyssa_ai_configuration",
        "nyssa_ai_logging",
    },
)

CORE_FORBIDDEN_PACKAGE_SLICES: Final = frozenset(
    {
        "records",
        "communications",
        "planning",
        "hosting",
        "transports",
        "cli",
        "launch_mcp",
        "logging_setup",
    },
)

FEATURE_SLICES: Final = frozenset({"records", "communications", "planning"})

BANNED_CLASS_OR_ALIAS_SUFFIX_RE: Final = re.compile(
    r"(?:DTO|Dto|Schema|Model|Input|Output|Class|Type|Object|Data|Port|Protocol|SourceRead)$",
)


def _iter_py_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if "__pycache__" not in p.parts)


def _imported_modules(py_file: Path, *, package_rel: tuple[str, ...]) -> list[tuple[int, str]]:
    tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
    imports: list[tuple[int, str]] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append((node.lineno, alias.name))
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                if node.module:
                    imports.append((node.lineno, node.module))
            else:
                # Resolve relative import against `daily_tasks.<package_rel>`
                anchor = ["daily_tasks", *package_rel[:-1]]
                up = node.level - 1
                base = anchor[: len(anchor) - up] if up > 0 else anchor
                resolved = ".".join([*base, node.module] if node.module else base)
                imports.append((node.lineno, resolved))
    return imports


def _rel_parts(py_file: Path) -> tuple[str, ...]:
    return py_file.relative_to(SRC_ROOT).parts


def test_no_retired_horizontal_layer_directories() -> None:
    offending = [
        str(d.relative_to(SRC_ROOT))
        for d in SRC_ROOT.rglob("*")
        if d.is_dir() and "__pycache__" not in d.parts and d.name in BANNED_DIRS
    ]
    assert offending == [], f"Banned horizontal directories present under src/daily_tasks: {offending}"


def test_core_is_pure_and_free_of_outer_or_transport_imports() -> None:
    violations: list[str] = []
    core_root = SRC_ROOT / "core"
    for py_file in _iter_py_files(core_root):
        rel = _rel_parts(py_file)
        for lineno, mod in _imported_modules(py_file, package_rel=rel):
            parts = mod.split(".")
            top = parts[0]
            if top in CORE_FORBIDDEN_EXTERNAL_ROOTS:
                violations.append(f"{'/'.join(rel)}:{lineno} imports forbidden external/OS module '{mod}'")
            elif top == "daily_tasks" and len(parts) >= 2 and parts[1] in CORE_FORBIDDEN_PACKAGE_SLICES:
                violations.append(f"{'/'.join(rel)}:{lineno} imports outer slice '{mod}'")
    assert violations == [], "\n".join(violations)


def test_core_subdomains_follow_acyclic_dependency_direction() -> None:
    """`core.records` -> `core.communications` -> `core.planning` must remain acyclic."""
    violations: list[str] = []
    for py_file in _iter_py_files(SRC_ROOT / "core"):
        rel = _rel_parts(py_file)
        if len(rel) < 2:
            continue
        subdomain = rel[1]
        for lineno, mod in _imported_modules(py_file, package_rel=rel):
            parts = mod.split(".")
            if len(parts) >= 3 and parts[0] == "daily_tasks" and parts[1] == "core":
                target_sub = parts[2]
                if subdomain == "records" and target_sub in {"communications", "planning"}:
                    violations.append(
                        f"{'/'.join(rel)}:{lineno} core.records must not import core.{target_sub} ({mod})"
                    )
                elif subdomain == "communications" and target_sub == "planning":
                    violations.append(
                        f"{'/'.join(rel)}:{lineno} core.communications must not import core.planning ({mod})",
                    )
    assert violations == [], "\n".join(violations)


def test_feature_slices_do_not_cross_import_or_depend_on_hosting_or_transports() -> None:
    violations: list[str] = []
    for slice_name in sorted(FEATURE_SLICES):
        slice_root = SRC_ROOT / slice_name
        for py_file in _iter_py_files(slice_root):
            rel = _rel_parts(py_file)
            for lineno, mod in _imported_modules(py_file, package_rel=rel):
                parts = mod.split(".")
                if parts[0] != "daily_tasks" or len(parts) < 2:
                    continue
                target = parts[1]
                sibling_slices = FEATURE_SLICES - {slice_name}
                if target in sibling_slices:
                    violations.append(
                        f"{'/'.join(rel)}:{lineno} slice '{slice_name}' cross-imports sibling '{target}' ({mod})",
                    )
                elif target in {"hosting", "transports", "cli", "launch_mcp"}:
                    violations.append(
                        f"{'/'.join(rel)}:{lineno} feature slice '{slice_name}' imports outer layer '{target}' ({mod})",
                    )
    assert violations == [], "\n".join(violations)


def test_transports_do_not_import_feature_slices_or_hosting() -> None:
    violations: list[str] = []
    transports_root = SRC_ROOT / "transports"
    forbidden = FEATURE_SLICES | {"hosting", "cli", "launch_mcp", "logging_setup"}
    for py_file in _iter_py_files(transports_root):
        rel = _rel_parts(py_file)
        for lineno, mod in _imported_modules(py_file, package_rel=rel):
            parts = mod.split(".")
            if parts[0] == "daily_tasks" and len(parts) >= 2 and parts[1] in forbidden:
                violations.append(f"{'/'.join(rel)}:{lineno} transport imports '{mod}'")
    assert violations == [], "\n".join(violations)


def test_no_banned_type_or_port_suffixes_in_src() -> None:
    violations: list[str] = []
    for py_file in _iter_py_files(SRC_ROOT):
        rel = "/".join(_rel_parts(py_file))
        tree = ast.parse(py_file.read_text(encoding="utf-8"), filename=str(py_file))
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef) and BANNED_CLASS_OR_ALIAS_SUFFIX_RE.search(node.name):
                violations.append(f"{rel}:{node.lineno} class '{node.name}' has banned suffix")
            elif isinstance(node, ast.TypeAlias) and isinstance(node.name, ast.Name):
                if BANNED_CLASS_OR_ALIAS_SUFFIX_RE.search(node.name.id):
                    violations.append(f"{rel}:{node.lineno} type alias '{node.name.id}' has banned suffix")
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
                ann = ast.unparse(node.annotation)
                if "TypeAlias" in ann and BANNED_CLASS_OR_ALIAS_SUFFIX_RE.search(node.target.id):
                    violations.append(f"{rel}:{node.lineno} TypeAlias '{node.target.id}' has banned suffix")
    assert violations == [], "\n".join(violations)
