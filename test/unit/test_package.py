"""Responsibility: Verify host manifest assembly, bundle hygiene, Hermes registration, and repository validation.
Public interface:
+-- ROOT
+-- test_build_packages_generates_matching_host_manifests_and_clean_bundles()
+-- test_hermes_adapter_registers_daily_tasks_skill(tmp_path)
+-- test_tree_excludes_private_state_directories(tmp_path)
`-- test_validate_repository_passes_canonical_source_and_catches_broken_links(tmp_path)

Package assembly and repository validation tests for `scripts/assemble.py` and `scripts/validate.py`.
"""

import importlib.util
import json
import shutil
import sys
from pathlib import Path
from types import ModuleType

ROOT = Path(__file__).resolve().parents[2]


def _load_script_module(name: str) -> ModuleType:
    scripts_dir = str(ROOT / "scripts")
    if scripts_dir not in sys.path:
        sys.path.insert(0, scripts_dir)
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_build_packages_generates_matching_host_manifests_and_clean_bundles() -> None:
    assemble_mod = _load_script_module("assemble")
    manifests, packages = assemble_mod.build_packages()
    identity = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))

    for host in ("claude", "codex", "cursor"):
        manifest = json.loads(manifests[f".{host}-plugin/plugin.json"])
        assert manifest["name"] == identity["name"]
        assert manifest["version"] == identity["version"]
        assert manifest["description"] == identity["description"]

    for fmt, files in packages.items():
        assert "skills/daily-tasks/SKILL.md" in files
        assert "src/daily_tasks/cli.py" in files
        assert "assembly.json" in files
        assert not any(
            name.startswith(("evals/", "docs/", "test/", "scripts/", ".temp/", ".nyssa-ai/")) for name in files
        ), f"Leak in {fmt}"

    portable_mcp = json.loads(packages["portable"]["mcp.json"])
    assert portable_mcp["mcpServers"]["daily-tasks"] == {
        "command": "python3",
        "args": ["./src/daily_tasks/launch_mcp.py"],
    }

    claude_mcp = json.loads(packages["portable"][".mcp.json"])
    assert claude_mcp["mcpServers"]["daily-tasks"] == {
        "command": "python3",
        "args": ["${CLAUDE_PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py"],
    }

    agy_mcp = json.loads(packages["antigravity"]["mcp_config.json"])
    assert agy_mcp["mcpServers"]["daily-tasks"] == {
        "command": "python3",
        "args": ["./src/daily_tasks/launch_mcp.py"],
        "disabled": False,
    }


def test_hermes_adapter_registers_daily_tasks_skill(tmp_path: Path) -> None:
    assemble_mod = _load_script_module("assemble")
    _, packages = assemble_mod.build_packages()
    hermes_files = packages["hermes"]

    for rel, content in hermes_files.items():
        if rel == "__init__.py" or rel.startswith("skills/"):
            dest = tmp_path / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(content, encoding="utf-8")

    spec = importlib.util.spec_from_file_location("daily_tasks_hermes", tmp_path / "__init__.py")
    assert spec is not None and spec.loader is not None
    hermes_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(hermes_mod)

    registered: list[tuple[str, Path]] = []

    class _Context:
        def register_skill(self, name: str, path: Path) -> None:
            registered.append((name, path))

    hermes_mod.register(_Context())
    assert [name for name, _ in registered] == ["daily-tasks"]
    assert registered[0][1].is_file()


def test_tree_excludes_private_state_directories(tmp_path: Path) -> None:
    assemble_mod = _load_script_module("assemble")
    (tmp_path / "daily-tasks").mkdir()
    (tmp_path / "daily-tasks" / "SKILL.md").write_text(
        "---\nname: daily-tasks\ndescription: ok\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "daily-tasks" / ".nyssa-ai").mkdir()
    (tmp_path / "daily-tasks" / ".nyssa-ai" / "profile.json").write_text("{}", encoding="utf-8")

    bundled = assemble_mod.tree(tmp_path, "skills/", exclude_private=True)
    assert "skills/daily-tasks/SKILL.md" in bundled
    assert not any(".nyssa-ai" in key for key in bundled)


def test_validate_repository_passes_canonical_source_and_catches_broken_links(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    assert validate_mod.validate_repository() == []

    # Verify broken link and README mismatch detection on a synthetic copy
    for filename in ("plugin.json", "pyproject.toml", "README.md", ".mcp.json"):
        shutil.copyfile(ROOT / filename, tmp_path / filename)
    (tmp_path / "adapters" / "hermes").mkdir(parents=True)
    shutil.copyfile(ROOT / "adapters" / "hermes" / "__init__.py", tmp_path / "adapters" / "hermes" / "__init__.py")
    shutil.copytree(ROOT / "skills", tmp_path / "skills")

    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / "README.md").write_text("# Daily Tasks\n\nVersion **0.0.1**\n", encoding="utf-8")
    skill_md = tmp_path / "skills" / "daily-tasks" / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8") + "\nBroken [missing](references/does-not-exist.md).\n",
        encoding="utf-8",
    )
    errors = validate_mod.validate_repository(tmp_path)
    assert any("README.md version mismatch" in err for err in errors)
    assert any("does-not-exist.md" in err for err in errors)
