"""Responsibility: Verify host manifest assembly, bundle hygiene, Hermes registration, evals report, and validation.
Public interface:
+-- ROOT
+-- test_assemble_check_allows_missing_default_dist_and_enforces_explicit_output_dir(tmp_path, monkeypatch)
+-- test_build_packages_generates_matching_host_manifests_and_clean_bundles()
+-- test_evals_report_check_hash_and_summary_counts(capsys)
+-- test_hermes_adapter_registers_daily_tasks_skill(tmp_path)
+-- test_mcp_config_bootstrapper_executes_help_via_uv(tmp_path)
+-- test_tree_excludes_private_state_directories(tmp_path)
+-- test_validate_repository_checks_evals_matrix_and_waza_manifests(tmp_path)
+-- test_validate_repository_enforces_apache_license_and_host_metadata_sync(tmp_path)
+-- test_validate_repository_enforces_docs_lockdown_codegraph_gitignore_and_link_stripping(tmp_path)
+-- test_validate_repository_enforces_evals_dir_lockdown_and_matrix_version_and_host_count(tmp_path)
+-- test_validate_repository_enforces_skill_bom_description_scope_verification_and_retired_openai_yaml(tmp_path)
+-- test_validate_repository_enforces_test_isolation(tmp_path)
+-- test_validate_repository_passes_canonical_source_and_catches_broken_links(tmp_path)
+-- test_validate_repository_rejects_retired_runtime_tokens_excluding_validator_itself(tmp_path)
`-- test_validate_repository_rejects_self_loaded_roots_loose_files_and_bad_gitattributes(tmp_path)

Package assembly, evaluation harness reporting, and repository validation tests.
"""

import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tomllib
from pathlib import Path
from types import ModuleType

import pytest

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


def _load_evals_report_module() -> ModuleType:
    spec = importlib.util.spec_from_file_location("daily_tasks_evals_report", ROOT / "evals" / "report.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _copy_repo_fixture(destination: Path) -> None:
    for filename in (
        ".gitattributes",
        ".gitignore",
        "plugin.json",
        "pyproject.toml",
        "LICENSE",
        "CHANGELOG.md",
        "README.md",
        ".mcp.json",
        "mcp.json",
        "mcp_config.json",
        "gemini-extension.json",
    ):
        shutil.copyfile(ROOT / filename, destination / filename)
    for host_rel in (
        ".claude-plugin/plugin.json",
        ".codex-plugin/plugin.json",
        ".cursor-plugin/plugin.json",
        ".tessl-plugin/plugin.json",
    ):
        target = destination / host_rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / host_rel, target)
    (destination / "harness-adapters" / "hermes").mkdir(parents=True)
    shutil.copyfile(
        ROOT / "harness-adapters" / "hermes" / "plugin.py",
        destination / "harness-adapters" / "hermes" / "plugin.py",
    )
    shutil.copytree(ROOT / "docs", destination / "docs", ignore=shutil.ignore_patterns("codegraph.db"))
    shutil.copytree(ROOT / "skills", destination / "skills")
    shutil.copytree(ROOT / "evals", destination / "evals")


def test_build_packages_generates_matching_host_manifests_and_clean_bundles() -> None:
    assemble_mod = _load_script_module("assemble")
    manifests, packages = assemble_mod.build_packages()
    identity = json.loads((ROOT / "plugin.json").read_text(encoding="utf-8"))
    pyproject = tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))

    assert identity["license"] == "Apache-2.0"
    assert pyproject["project"]["license"] == "Apache-2.0"
    license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")
    assert "Apache License" in license_text and "Copyright 2026 NyssaAI" in license_text
    assert (ROOT / "CHANGELOG.md").is_file()

    synced_fields = ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")
    for host in ("claude", "codex", "cursor"):
        manifest = json.loads(manifests[f".{host}-plugin/plugin.json"])
        for field in synced_fields:
            assert manifest[field] == identity[field]

    codex_interface = json.loads(manifests[".codex-plugin/plugin.json"])["interface"]
    assert codex_interface["capabilities"] == ["Interactive", "Read", "Write"]
    assert codex_interface["websiteURL"] == identity["homepage"]
    assert isinstance(codex_interface["defaultPrompt"], list) and codex_interface["defaultPrompt"]

    expected_tessl = {
        "name": "nyssa-ai/daily-tasks",
        "version": identity["version"],
        "description": identity["description"],
        "private": True,
        "skills": "./skills",
        "mcpServers": ".mcp.json",
    }
    assert json.loads(manifests[".tessl-plugin/plugin.json"]) == expected_tessl
    assert json.loads(packages["portable"][".tessl-plugin/plugin.json"]) == expected_tessl

    expected_gemini = {
        "name": "daily-tasks",
        "version": identity["version"],
        "description": identity["description"],
    }
    gemini_manifest = json.loads(manifests["gemini-extension.json"])
    assert "contextFileName" not in gemini_manifest
    assert gemini_manifest == expected_gemini
    assert json.loads(packages["portable"]["gemini-extension.json"]) == expected_gemini

    for fmt, files in packages.items():
        assert "skills/daily-tasks/SKILL.md" in files
        assert "src/daily_tasks/cli.py" in files
        assert "LICENSE" in files and "Apache License" in files["LICENSE"]
        assert "CHANGELOG.md" not in files
        assert "assembly.json" in files
        assert not any(
            name.startswith(("evals/", "docs/", "test/", "scripts/", ".temp/", ".nyssa-ai/")) for name in files
        ), f"Leak in {fmt}"
        for rel, content in files.items():
            assert "PLUGIN_DATA" not in content, f"Retired PLUGIN_DATA leaked into {fmt}/{rel}"

    portable_mcp = json.loads(packages["portable"]["mcp.json"])
    assert json.loads(manifests["mcp.json"]) == portable_mcp
    assert portable_mcp == {
        "$schema": "https://agent-plugins.org/schemas/1.0.0/mcp.schema.json",
        "mcpServers": {
            "daily-tasks": {
                "type": "stdio",
                "command": "uv",
                "args": [
                    "run",
                    "--no-project",
                    "python",
                    "${PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py",
                ],
            }
        },
    }

    claude_mcp = json.loads(packages["portable"][".mcp.json"])
    assert json.loads(manifests[".mcp.json"]) == claude_mcp
    assert claude_mcp["mcpServers"]["daily-tasks"] == {
        "command": "uv",
        "args": [
            "run",
            "--no-project",
            "python",
            "${CLAUDE_PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py",
        ],
    }

    agy_plugin = json.loads(packages["antigravity"]["plugin.json"])
    assert agy_plugin == {
        "name": identity["name"],
        "version": identity["version"],
        "description": identity["description"],
        "author": identity["author"],
        "homepage": identity["homepage"],
        "repository": identity["repository"],
    }

    agy_mcp = json.loads(packages["antigravity"]["mcp_config.json"])
    assert json.loads(manifests["mcp_config.json"]) == agy_mcp
    assert json.loads(packages["portable"]["mcp_config.json"]) == agy_mcp
    agy_srv = agy_mcp["mcpServers"]["daily-tasks"]
    assert agy_srv["command"] == "uv"
    assert agy_srv["args"][:4] == ["run", "--no-project", "python", "-c"]
    assert "runpy.run_path" in agy_srv["args"][4]


def test_mcp_config_bootstrapper_executes_help_via_uv(tmp_path: Path) -> None:
    assert shutil.which("uv") is not None
    cfg = json.loads((ROOT / "mcp_config.json").read_text(encoding="utf-8"))["mcpServers"]["daily-tasks"]
    runtime_root = tmp_path / "runtime"
    empty_home = tmp_path / "home"
    empty_home.mkdir()

    uv_cache_probe = subprocess.run(
        ["uv", "cache", "dir"],
        capture_output=True,
        text=True,
        check=False,
    )
    env = {k: v for k, v in os.environ.items() if k not in {"UV_PROJECT_ENVIRONMENT", "VIRTUAL_ENV"}}
    if uv_cache_probe.returncode == 0 and uv_cache_probe.stdout.strip():
        env.setdefault("UV_CACHE_DIR", uv_cache_probe.stdout.strip())
    env["HOME"] = str(empty_home)
    env["USERPROFILE"] = str(empty_home)
    env["PLUGIN_ROOT"] = "${PLUGIN_ROOT}"
    env.pop("DAILY_TASKS_PLUGIN_ROOT", None)
    env.pop("CLAUDE_PLUGIN_ROOT", None)
    env["NYSSA_RUNTIME_ROOT"] = str(runtime_root)

    proc = subprocess.run(
        [cfg["command"], *cfg["args"], "--help"],
        cwd=ROOT,
        env=env,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "usage: daily-tasks-mcp" in proc.stdout


def test_hermes_adapter_registers_daily_tasks_skill(tmp_path: Path) -> None:
    assert (ROOT / "harness-adapters" / "hermes" / "plugin.py").is_file()
    assert not (ROOT / "harness-adapters" / "hermes" / "__init__.py").exists()
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


def test_assemble_check_allows_missing_default_dist_and_enforces_explicit_output_dir(
    tmp_path: Path,
    monkeypatch: object,
) -> None:
    assemble_mod = _load_script_module("assemble")
    unpopulated_default = tmp_path / "unpopulated-default-dist"
    monkeypatch.setattr(assemble_mod, "DEFAULT_DIST_DIR", unpopulated_default)  # type: ignore[attr-defined]
    assert assemble_mod.assemble(["check"]) == 0
    assert not unpopulated_default.exists()

    explicit_missing = tmp_path / "explicit-missing-dist"
    assert assemble_mod.assemble(["check", "--output-dir", str(explicit_missing)]) == 1

    staged = tmp_path / "staged-dist"
    assert assemble_mod.assemble(["write", "--output-dir", str(staged)]) == 0
    assert assemble_mod.assemble(["check", "--output-dir", str(staged)]) == 0
    (staged / "portable" / "unexpected.txt").write_text("drift\n", encoding="utf-8")
    assert assemble_mod.assemble(["check", "--output-dir", str(staged)]) == 1


def test_tree_excludes_private_state_directories(tmp_path: Path) -> None:
    assemble_mod = _load_script_module("assemble")
    (tmp_path / "daily-tasks").mkdir()
    (tmp_path / "daily-tasks" / "SKILL.md").write_text(
        "---\nname: daily-tasks\ndescription: ok\n---\n",
        encoding="utf-8",
    )
    (tmp_path / "daily-tasks" / ".nyssa-ai").mkdir()
    (tmp_path / "daily-tasks" / ".nyssa-ai" / "config.json").write_text("{}", encoding="utf-8")

    bundled = assemble_mod.tree(tmp_path, "skills/", exclude_private=True)
    assert "skills/daily-tasks/SKILL.md" in bundled
    assert not any(".nyssa-ai" in key for key in bundled)


def test_validate_repository_passes_canonical_source_and_catches_broken_links(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    assert validate_mod.validate_repository() == []

    # Verify broken link, retired files, and manifest validation on a synthetic copy
    _copy_repo_fixture(tmp_path)
    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / "README.md").write_text("# Daily Tasks\n\nVersion **0.0.1**\n", encoding="utf-8")
    (tmp_path / "gemini-extension.json").write_text(
        json.dumps({"name": "daily-tasks", "version": "0.11.3", "description": "x", "contextFileName": "GEMINI.md"}),
        encoding="utf-8",
    )
    (tmp_path / "harness-adapters" / "hermes" / "__init__.py").write_text("# retired\n", encoding="utf-8")
    skill_md = tmp_path / "skills" / "daily-tasks" / "SKILL.md"
    skill_md.write_text(
        skill_md.read_text(encoding="utf-8") + "\nBroken [missing](references/does-not-exist.md).\n",
        encoding="utf-8",
    )
    errors = validate_mod.validate_repository(tmp_path)
    assert any("README.md version mismatch" in err for err in errors)
    assert any("contextFileName" in err for err in errors)
    assert any("harness-adapters/hermes/__init__.py" in err for err in errors)
    assert any("does-not-exist.md" in err for err in errors)


def test_validate_repository_enforces_apache_license_and_host_metadata_sync(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)
    assert validate_mod.validate_repository(tmp_path) == []

    # Remove LICENSE and introduce pyproject license mismatch + host metadata drift
    (tmp_path / "LICENSE").unlink()
    (tmp_path / "README.md").write_text("# Daily Tasks\n\nVersion **0.11.3**\n", encoding="utf-8")
    (tmp_path / "pyproject.toml").write_text(
        (tmp_path / "pyproject.toml").read_text(encoding="utf-8").replace('license = "Apache-2.0"', 'license = "MIT"'),
        encoding="utf-8",
    )
    claude_data = json.loads((tmp_path / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    claude_data["license"] = "MIT"
    (tmp_path / ".claude-plugin" / "plugin.json").write_text(json.dumps(claude_data, indent=2), encoding="utf-8")

    codex_data = json.loads((tmp_path / ".codex-plugin" / "plugin.json").read_text(encoding="utf-8"))
    codex_data["author"] = {"name": "OtherOrg"}
    (tmp_path / ".codex-plugin" / "plugin.json").write_text(json.dumps(codex_data, indent=2), encoding="utf-8")

    cursor_data = json.loads((tmp_path / ".cursor-plugin" / "plugin.json").read_text(encoding="utf-8"))
    cursor_data["keywords"] = ["drift"]
    (tmp_path / ".cursor-plugin" / "plugin.json").write_text(json.dumps(cursor_data, indent=2), encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert any("Missing LICENSE at repo_root" in err for err in errors)
    assert any("License mismatch" in err for err in errors)
    assert any("Metadata drift in .claude-plugin/plugin.json" in err for err in errors)
    assert any("Metadata drift in .codex-plugin/plugin.json" in err for err in errors)
    assert any("Metadata drift in .cursor-plugin/plugin.json" in err for err in errors)


def test_evals_report_check_hash_and_summary_counts(capsys: pytest.CaptureFixture[str]) -> None:
    report_mod = _load_evals_report_module()

    assert report_mod.main(["hash"]) == 0
    digest_out = capsys.readouterr().out.strip()
    assert len(digest_out) == 64
    assert digest_out == report_mod.candidate_sha256()

    assert report_mod.main(["check"]) == 0
    check_out = capsys.readouterr().out.strip()
    assert "Report consistent" in check_out

    assert report_mod.main(["release"]) == 1
    capsys.readouterr()

    assert report_mod.main(["summary", "--no-code-tests"]) == 0
    summary_payload = json.loads(capsys.readouterr().out)
    assert summary_payload["candidate_sha256"] == digest_out
    assert summary_payload["suite_revision"] == "0.11.3"
    assert summary_payload["release_ready"] is False
    assert "code_tests" not in summary_payload["suites"]
    assert summary_payload["suites"]["host_matrix"]["total"] == 11
    assert summary_payload["suites"]["waza"]["total"] == 19
    assert summary_payload["suites"]["waza"]["not_run"] == 19
    manifests = [entry["manifest"] for entry in summary_payload["waza"]]
    assert manifests == [
        "evals/waza/skills/daily-tasks/eval.yaml",
        "evals/waza/skills/daily-tasks/behavior.yaml",
    ]

    latest_md = (ROOT / "evals" / "LATEST.md").read_text(encoding="utf-8")
    assert "# Latest plugin evaluation" in latest_md
    assert f"Candidate SHA-256: `{digest_out}`" in latest_md
    assert "../.temp/" not in latest_md


def test_validate_repository_checks_evals_matrix_and_waza_manifests(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)
    assert validate_mod.validate_repository(tmp_path) == []

    # Duplicate matrix row + list-formatted Waza task + invalid trigger skill_path + missing LATEST.md
    matrix_data = json.loads((tmp_path / "evals" / "matrix.json").read_text(encoding="utf-8"))
    matrix_data["rows"].append(dict(matrix_data["rows"][0]))
    (tmp_path / "evals" / "matrix.json").write_text(json.dumps(matrix_data, indent=2), encoding="utf-8")
    (tmp_path / "evals" / "LATEST.md").unlink()
    (tmp_path / "evals" / "waza" / "skills" / "daily-tasks" / "tasks" / "in-scope.yaml").write_text(
        "- id: list-not-dict\n  name: wrong\n",
        encoding="utf-8",
    )
    (tmp_path / "evals" / "waza" / "skills" / "daily-tasks" / "tasks" / "plan-in-scope.yaml").write_text(
        (
            "id: bad-trigger\n"
            "name: Bad trigger\n"
            "inputs:\n"
            "  prompt: Plan my day\n"
            "graders:\n"
            "  - type: trigger\n"
            "    name: bad\n"
            "    config:\n"
            "      skill_path: skills/missing/SKILL.md\n"
            "      mode: invalid\n"
        ),
        encoding="utf-8",
    )

    errors = validate_mod.validate_repository(tmp_path)
    assert any("Duplicate row key in evals/matrix.json" in err for err in errors)
    assert any("Missing evals/LATEST.md" in err for err in errors)
    assert any("must be a single TestCase mapping (dict)" in err for err in errors)
    assert any("Malformed trigger grader" in err for err in errors)


def test_validate_repository_rejects_self_loaded_roots_loose_files_and_bad_gitattributes(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)
    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / ".agents").mkdir()
    (tmp_path / ".hermes").mkdir()
    (tmp_path / "adapters").mkdir()
    (tmp_path / "artifacts").mkdir()
    (tmp_path / "unexpected-top-dir").mkdir()
    (tmp_path / "GLOSSARY.md").write_text("# Retired root glossary\n", encoding="utf-8")
    (tmp_path / ".gitattributes").write_text("*.db binary\n", encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert any(".agents/" in err for err in errors)
    assert any(".hermes/" in err for err in errors)
    assert any("Retired adapters/" in err for err in errors)
    assert any("Retired artifacts/" in err for err in errors)
    assert any("unexpected-top-dir/" in err for err in errors)
    assert any("GLOSSARY.md" in err for err in errors)
    assert any("eol=lf" in err for err in errors)

    (tmp_path / ".gitattributes").unlink()
    missing_gitattr_errors = validate_mod.validate_repository(tmp_path)
    assert any("Missing .gitattributes at repo_root" in err for err in missing_gitattr_errors)


def test_validate_repository_enforces_docs_lockdown_codegraph_gitignore_and_link_stripping(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)

    glossary = tmp_path / "docs" / "GLOSSARY.md"
    original_glossary = glossary.read_text(encoding="utf-8")
    glossary.write_text(
        original_glossary
        + "\n<!-- [commented](missing-comment.md) -->\n"
        + "Inline code `[code-link](missing-inline.md)` is ignored.\n"
        + "```markdown\n[fenced-link](missing-fenced.md)\n```\n",
        encoding="utf-8",
    )
    assert validate_mod.validate_repository(tmp_path) == []

    # Real broken link, disallowed docs files/dirs, gitignored docs/, and src/ without codegraph.db
    glossary.unlink()
    (tmp_path / "docs" / "product.md").write_text(
        (tmp_path / "docs" / "product.md").read_text(encoding="utf-8") + "\nSee [broken](missing-doc.md).\n",
        encoding="utf-8",
    )
    (tmp_path / "docs" / "roadmap.md").write_text("# Disallowed\n", encoding="utf-8")
    (tmp_path / "docs" / "reviews").mkdir()
    (tmp_path / "docs" / "specs" / "prose.md").write_text("# Not JSON\n", encoding="utf-8")
    (tmp_path / ".gitignore").write_text(".temp/\ndocs/\n", encoding="utf-8")
    (tmp_path / "src").mkdir()

    errors = validate_mod.validate_repository(tmp_path)
    assert any("Missing mandatory docs/GLOSSARY.md" in err for err in errors)
    assert any("missing-doc.md" in err for err in errors)
    assert not any("missing-comment.md" in err for err in errors)
    assert not any("missing-inline.md" in err for err in errors)
    assert not any("missing-fenced.md" in err for err in errors)
    assert any("docs/roadmap.md" in err for err in errors)
    assert any("docs/reviews/" in err for err in errors)
    assert any("docs/specs/prose.md" in err for err in errors)
    assert any(".gitignore must not ignore docs/" in err for err in errors)
    assert any("docs/code-map/codegraph.db" in err for err in errors)


def test_validate_repository_enforces_test_isolation(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)

    (tmp_path / "test" / "unit").mkdir(parents=True)
    (tmp_path / "test" / "use_case").mkdir(parents=True)
    (tmp_path / "test" / "e2e").mkdir(parents=True)
    (tmp_path / "test" / "unit" / "test_ok.py").write_text(
        "def test_ok() -> None:\n    assert True\n",
        encoding="utf-8",
    )
    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / "test" / "test_loose.py").write_text("def test_loose() -> None:\n    pass\n", encoding="utf-8")
    (tmp_path / "test" / "integration").mkdir()
    (tmp_path / "docs" / "code-map").mkdir(exist_ok=True)
    (tmp_path / "docs" / "code-map" / "codegraph.db").write_bytes(b"sqlite")
    (tmp_path / "src" / "daily_tasks").mkdir(parents=True)
    (tmp_path / "src" / "daily_tasks" / "test_comingled.py").write_text("# bad\n", encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert any("test/test_loose.py" in err for err in errors)
    assert any("test/integration/" in err for err in errors)
    assert any("src/daily_tasks/test_comingled.py" in err for err in errors)


def test_validate_repository_enforces_skill_bom_description_scope_verification_and_retired_openai_yaml(
    tmp_path: Path,
) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)
    assert validate_mod.validate_repository(tmp_path) == []

    cli_ref = tmp_path / "skills" / "daily-tasks" / "references" / "cli.md"
    cli_ref.write_text(
        "\ufeff" + cli_ref.read_text(encoding="utf-8").replace("> [!IMPORTANT] Scope Directive", "> Note"),
        encoding="utf-8",
    )
    capture_wf = tmp_path / "skills" / "daily-tasks" / "workflows" / "capture.md"
    capture_wf.write_text(
        capture_wf.read_text(encoding="utf-8")
        .replace("> [!IMPORTANT] Scope Directive", "> Note")
        .replace("## Verification", "## Done"),
        encoding="utf-8",
    )
    skill_md = tmp_path / "skills" / "daily-tasks" / "SKILL.md"
    long_desc = "x" * 1025
    skill_md.write_text(
        f"---\nname: daily-tasks\ndescription: {long_desc}\n---\n\n# Daily Tasks\n",
        encoding="utf-8",
    )
    (tmp_path / "skills" / "daily-tasks" / "agents").mkdir()
    (tmp_path / "skills" / "daily-tasks" / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")
    (tmp_path / "harness-adapters" / "codex" / "agents").mkdir(parents=True)
    (tmp_path / "harness-adapters" / "codex" / "agents" / "openai.yaml").write_text("interface: {}\n", encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert any("UTF-8 BOM is forbidden in skills/daily-tasks/references/cli.md" in err for err in errors)
    assert any("Missing Scope Directive in skills/daily-tasks/references/cli.md" in err for err in errors)
    assert any("Missing Scope Directive in skills/daily-tasks/workflows/capture.md" in err for err in errors)
    assert any("Missing ## Verification section in skills/daily-tasks/workflows/capture.md" in err for err in errors)
    assert any("Skill description exceeds 1024 characters: skills/daily-tasks/SKILL.md" in err for err in errors)
    assert any("Missing Scope Directive in skills/daily-tasks/SKILL.md" in err for err in errors)
    assert any("Missing ## Verification section in skills/daily-tasks/SKILL.md" in err for err in errors)
    assert any("skills/daily-tasks/agents/" in err for err in errors)
    assert any("harness-adapters/codex/agents/openai.yaml" in err for err in errors)


def test_validate_repository_rejects_retired_runtime_tokens_excluding_validator_itself(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)
    (tmp_path / "scripts").mkdir()
    shutil.copyfile(ROOT / "scripts" / "validate.py", tmp_path / "scripts" / "validate.py")
    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / "docs" / "code-map").mkdir(exist_ok=True)
    (tmp_path / "docs" / "code-map" / "codegraph.db").write_bytes(b"sqlite")
    (tmp_path / "src").mkdir()
    (tmp_path / "src" / "legacy.py").write_text('ENV_KEY = "NYSSA_PLUGIN_STATE_DIR"\n', encoding="utf-8")
    (tmp_path / "skills" / "daily-tasks" / "assets" / "settings.schema.json").write_text("{}\n", encoding="utf-8")
    (tmp_path / "scripts" / "helper.py").write_text('# references settings.schema.json\n', encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert not any("scripts/validate.py" in err for err in errors)
    assert any("NYSSA_PLUGIN_STATE_DIR" in err and "src/legacy.py" in err for err in errors)
    assert any(
        "settings.schema.json" in err and "skills/daily-tasks/assets/settings.schema.json" in err for err in errors
    )
    assert any("settings.schema.json" in err and "scripts/helper.py" in err for err in errors)


def test_validate_repository_enforces_evals_dir_lockdown_and_matrix_version_and_host_count(tmp_path: Path) -> None:
    validate_mod = _load_script_module("validate")
    _copy_repo_fixture(tmp_path)

    (tmp_path / "evals" / "verifiers").mkdir()
    (tmp_path / "evals" / "__pycache__").mkdir(exist_ok=True)
    assert validate_mod.validate_repository(tmp_path) == []

    (tmp_path / "evals" / "evidence").mkdir()
    (tmp_path / "evals" / "adhoc-dump").mkdir()
    matrix_path = tmp_path / "evals" / "matrix.json"
    matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
    matrix_data["version"] = "0.0.1"
    matrix_data["rows"] = matrix_data["rows"][:10]
    matrix_path.write_text(json.dumps(matrix_data, indent=2), encoding="utf-8")

    errors = validate_mod.validate_repository(tmp_path)
    assert any("evals/evidence/" in err for err in errors)
    assert any("evals/adhoc-dump/" in err for err in errors)
    assert any("evals/matrix.json version" in err for err in errors)
    assert any("11 unique host rows" in err for err in errors)
