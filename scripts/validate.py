"""Responsibility: Validate canonical repo layout, skills, docs lockdown, relative links, adapters, evals, and parity.
Public interface:
+-- validate()
`-- validate_repository(root)
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tomllib
from pathlib import Path

import yaml  # type: ignore[import-untyped]
from assemble import ROOT, tree

_FRONTMATTER_BLOCK_RE = re.compile(r"\A---\n(.*?)\n---(?:\n|$)", re.DOTALL)
_SKILL_NAME_RE = re.compile(r"^[a-z0-9-]+$")
_FENCED_CODE_RE = re.compile(r"^([ \t]*)(`{3,}|~{3,})[^\n]*\n[\s\S]*?^\1\2[ \t]*$", re.MULTILINE)
_HTML_COMMENT_RE = re.compile(r"<!--[\s\S]*?-->")
_INLINE_CODE_RE = re.compile(r"(`+)(?:(?!\1)[^\n])+?\1")
_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")
_URI_SCHEME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9+.-]+:")
_LEAK_RE = re.compile(r"C:[\\/]|D:[\\/]|\.codex/plugins/cache")
_VERIFICATION_HEADING_RE = re.compile(r"^##\s+(?:\d+\.\s+)?Verification\b", re.MULTILINE)
_TEST_FILE_RE = re.compile(r"^(?:test_.*\.py|.*_test\.py)$")

_SCOPE_DIRECTIVE = "> [!IMPORTANT] Scope Directive"
_CACHE_DIRS = frozenset({"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"})
_FORBIDDEN_SELF_LOADED_DIRS = frozenset({".agents", ".hermes"})
_RETIRED_ROOT_DIRS: dict[str, str] = {
    "adapters": "Retired adapters/ directory must not exist; use harness-adapters/",
    "artifacts": "Retired artifacts/ directory must not exist; stage bundles into .temp/dist/",
    "plugins": "Nested plugins/ directory must not exist at repo_root",
}
_ALLOWED_ROOT_DIRS = frozenset(
    {
        "skills",
        "src",
        "test",
        "evals",
        "docs",
        "scripts",
        "harness-adapters",
        "rules",
        "commands",
        "hooks",
        ".temp",
        ".github",
        ".nyssa-ai",
        ".claude-plugin",
        ".codex-plugin",
        ".cursor-plugin",
        ".tessl-plugin",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        ".worktrees",
        ".vscode",
        ".idea",
    }
)
_ALLOWED_ROOT_FILES = frozenset(
    {
        ".gitattributes",
        ".gitignore",
        ".mcp.json",
        "AGENTS.md",
        "CHANGELOG.md",
        "CLAUDE.md",
        "GEMINI.md",
        "LICENSE",
        "README.md",
        "gemini-extension.json",
        "mcp.json",
        "mcp_config.json",
        "plugin.json",
        "pyproject.toml",
        "uv.lock",
    }
)
_ALLOWED_DOCS_FILES = frozenset({"GLOSSARY.md", "product.md", "features.md", "tech-stack.md"})
_ALLOWED_DOCS_DIRS = frozenset({"concepts", "features", "plans", "learnings", "specs", "code-map"})
_ALLOWED_TEST_DIRS = frozenset({"unit", "use_case", "e2e"})
_ALLOWED_TEST_ROOT_FILES = frozenset({"__init__.py", "conftest.py"})
_ALLOWED_EVALS_DIRS = frozenset({"waza", "tessl", "scenarios", "reports", "verifiers"})
_DISALLOWED_EVALS_DIRS = frozenset({"suites", "evidence", "results", "attempts"})
_RETIRED_RUNTIME_TOKENS = ("NYSSA_PLUGIN_STATE_DIR", "settings.schema.json")


def _load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _load_yaml_text(text: str) -> object:
    return yaml.safe_load(text)


def _strip_markdown_code_and_comments(content: str) -> str:
    without_fences = _FENCED_CODE_RE.sub("", content)
    without_comments = _HTML_COMMENT_RE.sub("", without_fences)
    return _INLINE_CODE_RE.sub("", without_comments)


def _validate_markdown_links(root: Path, rel_name: str, content: str, errors: list[str]) -> None:
    resolved_root = root.resolve()
    temp_root = (root / ".temp").resolve()
    stripped = _strip_markdown_code_and_comments(content)
    for match in _LINK_RE.finditer(stripped):
        raw_target = match.group(1).strip()
        if not raw_target or raw_target.startswith("#") or _URI_SCHEME_RE.match(raw_target):
            continue
        target_part = raw_target.split("#", 1)[0].strip().strip("<>")
        if not target_part:
            continue
        target = (root / Path(rel_name).parent / target_part).resolve()
        if not target.is_relative_to(resolved_root):
            errors.append(f"Escaping link: {rel_name}")
            continue
        if target.is_relative_to(temp_root):
            errors.append(f"Ephemeral .temp link in {rel_name}: {raw_target}")
            continue
        if not target.exists():
            errors.append(f"Broken link in {rel_name}: {raw_target}")


def _is_git_ignored(root: Path, rel_path: str) -> bool:
    if not (root / ".git").exists():
        return False
    try:
        proc = subprocess.run(
            ["git", "check-ignore", "-q", rel_path],
            cwd=root,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
        )
        return proc.returncode == 0
    except OSError:
        return False


def _validate_root_layout_and_gitattributes(root: Path, is_assembled: bool, errors: list[str]) -> None:
    if not root.is_dir():
        return
    for item in sorted(root.iterdir(), key=lambda p: p.name):
        if item.is_dir():
            if item.name in _FORBIDDEN_SELF_LOADED_DIRS:
                errors.append(f"Forbidden self-loaded host directory at repo_root: {item.name}/")
            elif item.name in _RETIRED_ROOT_DIRS:
                errors.append(_RETIRED_ROOT_DIRS[item.name])
            elif not is_assembled and item.name not in _ALLOWED_ROOT_DIRS:
                errors.append(f"Unexpected non-canonical top-level directory at repo_root: {item.name}/")
        elif not is_assembled and item.name not in _ALLOWED_ROOT_FILES:
            errors.append(f"Unexpected loose file at repo_root: {item.name}")

    if not is_assembled:
        gitattributes_path = root / ".gitattributes"
        if not gitattributes_path.is_file():
            errors.append("Missing .gitattributes at repo_root")
        else:
            active_lines = [
                line.strip()
                for line in gitattributes_path.read_text(encoding="utf-8").splitlines()
                if line.strip() and not line.lstrip().startswith("#")
            ]
            if not any("eol=lf" in line for line in active_lines):
                errors.append(".gitattributes at repo_root must contain eol=lf")


def _validate_docs(root: Path, is_assembled: bool, errors: list[str]) -> None:
    docs_dir = root / "docs"
    if not is_assembled:
        gitignore_path = root / ".gitignore"
        if not gitignore_path.is_file():
            errors.append("Missing .gitignore at repo_root")
        else:
            for raw_line in gitignore_path.read_text(encoding="utf-8").splitlines():
                pattern = raw_line.strip()
                if not pattern or pattern.startswith(("#", "!")):
                    continue
                normalized = pattern.lstrip("/").rstrip("/").removesuffix("/*").removesuffix("/**")
                if normalized in {"docs", "docs/GLOSSARY.md", "docs/code-map", "docs/code-map/codegraph.db"}:
                    errors.append(f".gitignore must not ignore docs/: {pattern}")
        if docs_dir.exists() and _is_git_ignored(root, "docs"):
            errors.append("docs/ directory must not be gitignored")
        if not (docs_dir / "GLOSSARY.md").is_file():
            errors.append("Missing mandatory docs/GLOSSARY.md")
        if (root / "src").is_dir() and not (docs_dir / "code-map" / "codegraph.db").is_file():
            errors.append("Missing mandatory docs/code-map/codegraph.db when src/ exists")

    if not docs_dir.is_dir():
        return

    for item in sorted(docs_dir.iterdir(), key=lambda p: p.name):
        if item.is_file() and item.name not in _ALLOWED_DOCS_FILES:
            errors.append(f"Disallowed file in docs/: docs/{item.name}")
        elif item.is_dir() and item.name not in _ALLOWED_DOCS_DIRS:
            errors.append(f"Disallowed directory in docs/: docs/{item.name}/")

    specs_dir = docs_dir / "specs"
    if specs_dir.is_dir():
        for spec_md in sorted(specs_dir.rglob("*.md")):
            errors.append(f"Disallowed Markdown file in docs/specs/: {spec_md.relative_to(root).as_posix()}")

    for md_path in sorted(docs_dir.rglob("*.md")):
        rel_md = md_path.relative_to(root).as_posix()
        md_content = md_path.read_text(encoding="utf-8")
        _validate_markdown_links(root, rel_md, md_content, errors)


def _validate_test_isolation(root: Path, errors: list[str]) -> None:
    test_dir = root / "test"
    if test_dir.is_dir():
        for item in sorted(test_dir.iterdir(), key=lambda p: p.name):
            if item.is_file():
                if _TEST_FILE_RE.match(item.name):
                    errors.append(
                        f"Loose test file at test/ root: test/{item.name}; "
                        "place tests under test/unit/, test/use_case/, or test/e2e/"
                    )
                elif item.name not in _ALLOWED_TEST_ROOT_FILES:
                    errors.append(f"Unexpected loose file at test/ root: test/{item.name}")
            elif item.is_dir() and item.name not in _ALLOWED_TEST_DIRS and item.name not in _CACHE_DIRS:
                if not item.name.startswith("."):
                    errors.append(
                        f"Non-canonical test subdirectory: test/{item.name}/; expected unit/, use_case/, or e2e/"
                    )

    for sub_name in ("src", "skills", "scripts", "harness-adapters"):
        sub_dir = root / sub_name
        if not sub_dir.is_dir():
            continue
        for py_file in sorted(sub_dir.rglob("*.py")):
            if any(part in _CACHE_DIRS or part in {".temp", ".nyssa-ai"} for part in py_file.relative_to(root).parts):
                continue
            if _TEST_FILE_RE.match(py_file.name):
                errors.append(f"Co-mingled test file outside test/: {py_file.relative_to(root).as_posix()}")


def _validate_skills(root: Path, errors: list[str]) -> set[str]:
    skills_root = root / "skills"
    if skills_root.is_dir():
        for skill_dir in sorted(skills_root.iterdir(), key=lambda p: p.name):
            if skill_dir.is_dir() and (skill_dir / "agents").exists():
                errors.append(f"Retired skills/{skill_dir.name}/agents/ directory must not exist")
        for openai_yaml in sorted(skills_root.rglob("openai.yaml")):
            rel_openai = openai_yaml.relative_to(root).as_posix()
            errors.append(f"Retired openai.yaml must not exist under skills/: {rel_openai}")
        for candidate in sorted(skills_root.rglob("*")):
            if any(part in {".nyssa-ai", ".nyssaai", ".nyssa", ".temp"} for part in candidate.relative_to(root).parts):
                errors.append(
                    f"Private state directory must not exist under skills/: {candidate.relative_to(root).as_posix()}"
                )

    codex_adapter_dir = root / "harness-adapters" / "codex"
    if codex_adapter_dir.exists():
        for openai_yaml in sorted(codex_adapter_dir.rglob("openai.yaml")):
            errors.append(
                f"Retired Codex openai.yaml must not exist: {openai_yaml.relative_to(root).as_posix()}"
            )

    files = tree(skills_root, "skills/")
    names: set[str] = set()
    for name, content in files.items():
        if name.endswith(".md") and "\ufeff" in content:
            errors.append(f"UTF-8 BOM is forbidden in {name}")
        clean_content = content.lstrip("\ufeff")
        rel_parts = Path(name).parts

        if name.endswith("/SKILL.md") and len(rel_parts) == 3:
            expected_dir = rel_parts[1]
            fm_match = _FRONTMATTER_BLOCK_RE.match(clean_content)
            try:
                fm_data = _load_yaml_text(fm_match.group(1)) if fm_match is not None else None
            except yaml.YAMLError:
                fm_data = None
            skill_name = fm_data.get("name") if isinstance(fm_data, dict) else None
            skill_desc = fm_data.get("description") if isinstance(fm_data, dict) else None
            if (
                not isinstance(skill_name, str)
                or not _SKILL_NAME_RE.match(skill_name)
                or skill_name != expected_dir
                or skill_name in names
                or not isinstance(skill_desc, str)
                or not skill_desc.strip()
            ):
                errors.append(f"Invalid skill frontmatter: {name}")
            else:
                names.add(skill_name)
                if len(skill_desc.strip()) > 1024:
                    errors.append(f"Skill description exceeds 1024 characters: {name}")
            if _SCOPE_DIRECTIVE not in clean_content:
                errors.append(f"Missing Scope Directive in {name}")
            if not _VERIFICATION_HEADING_RE.search(clean_content):
                errors.append(f"Missing ## Verification section in {name}")
        elif len(rel_parts) == 4 and rel_parts[2] == "workflows" and name.endswith(".md"):
            if _SCOPE_DIRECTIVE not in clean_content:
                errors.append(f"Missing Scope Directive in {name}")
            if not _VERIFICATION_HEADING_RE.search(clean_content):
                errors.append(f"Missing ## Verification section in {name}")
        elif len(rel_parts) == 4 and rel_parts[2] == "references" and name.endswith(".md"):
            if _SCOPE_DIRECTIVE not in clean_content:
                errors.append(f"Missing Scope Directive in {name}")

        if name.endswith(".md"):
            _validate_markdown_links(root, name, clean_content, errors)
        if _LEAK_RE.search(clean_content):
            errors.append(f"Local path leaked: {name}")

    return names


def _validate_retired_runtime_tokens(root: Path, errors: list[str]) -> None:
    for sub_name in ("src", "skills", "scripts", "harness-adapters"):
        sub_dir = root / sub_name
        if not sub_dir.is_dir():
            continue
        for file_path in sorted(sub_dir.rglob("*")):
            if not file_path.is_file() or file_path.is_symlink():
                continue
            rel_parts = file_path.relative_to(root).parts
            if any(part in _CACHE_DIRS or part in {".temp", ".nyssa-ai"} for part in rel_parts):
                continue
            rel_posix = file_path.relative_to(root).as_posix()
            if rel_posix == "scripts/validate.py":
                continue
            if file_path.name == "settings.schema.json":
                errors.append(f"Retired settings.schema.json must not exist: {rel_posix}")
            try:
                text = file_path.read_text(encoding="utf-8")
            except UnicodeDecodeError:
                continue
            for token in _RETIRED_RUNTIME_TOKENS:
                if token in text:
                    errors.append(f"Retired runtime token {token!r} found in {rel_posix}")


def _validate_waza_manifest(root: Path, manifest_rel: str, errors: list[str]) -> None:
    manifest_path = root / manifest_rel
    if not manifest_path.is_file():
        errors.append(f"Missing {manifest_rel}")
        return
    try:
        raw_manifest = _load_yaml(manifest_path)
    except (OSError, yaml.YAMLError) as exc:
        errors.append(f"Invalid YAML in {manifest_rel}: {exc}")
        return
    if not isinstance(raw_manifest, dict) or raw_manifest.get("skill") != "daily-tasks":
        errors.append(f"Malformed {manifest_rel}: must be a mapping declaring skill: daily-tasks")
        return
    task_patterns = raw_manifest.get("tasks")
    if not isinstance(task_patterns, list) or not task_patterns or not all(isinstance(p, str) for p in task_patterns):
        errors.append(f"Malformed {manifest_rel}: tasks must be a non-empty list of glob strings")
        return
    matched_files: list[Path] = []
    for pattern in task_patterns:
        for candidate in sorted(manifest_path.parent.glob(pattern)):
            if candidate.is_file() and candidate not in matched_files:
                matched_files.append(candidate)
    if not matched_files:
        errors.append(f"Malformed {manifest_rel}: tasks globs resolved 0 task files")
        return
    for task_file in matched_files:
        task_rel = task_file.relative_to(root).as_posix()
        try:
            raw_task = _load_yaml(task_file)
        except (OSError, yaml.YAMLError) as exc:
            errors.append(f"Invalid YAML in {task_rel}: {exc}")
            continue
        if not isinstance(raw_task, dict):
            errors.append(f"Malformed Waza task {task_rel}: must be a single TestCase mapping (dict)")
            continue
        task_id = raw_task.get("id")
        task_name = raw_task.get("name")
        inputs = raw_task.get("inputs")
        prompt = inputs.get("prompt") if isinstance(inputs, dict) else None
        graders = raw_task.get("graders")
        if (
            not isinstance(task_id, str)
            or not task_id.strip()
            or not isinstance(task_name, str)
            or not task_name.strip()
            or not isinstance(prompt, str)
            or not prompt.strip()
            or not isinstance(graders, list)
            or not graders
            or not all(isinstance(g, dict) for g in graders)
        ):
            errors.append(f"Malformed Waza task {task_rel}: requires id, name, inputs.prompt, and graders")
            continue
        for grader in graders:
            if grader.get("type") == "trigger":
                cfg = grader.get("config")
                skill_path = cfg.get("skill_path") if isinstance(cfg, dict) else None
                mode = cfg.get("mode") if isinstance(cfg, dict) else None
                if (
                    not isinstance(skill_path, str)
                    or not skill_path.strip()
                    or not (root / skill_path).is_file()
                    or mode not in {"positive", "negative"}
                ):
                    errors.append(
                        f"Malformed trigger grader in {task_rel}: requires existing config.skill_path and valid mode"
                    )


def _validate_evals(root: Path, identity: dict[str, object], errors: list[str]) -> None:
    evals_dir = root / "evals"
    if not evals_dir.is_dir():
        errors.append("Missing evals/ directory")
        return
    for child in sorted(evals_dir.iterdir(), key=lambda p: p.name):
        if not child.is_dir() or child.name in _CACHE_DIRS:
            continue
        if child.name in _DISALLOWED_EVALS_DIRS:
            errors.append(f"Disallowed ephemeral directory in evals/: evals/{child.name}/")
        elif child.name not in _ALLOWED_EVALS_DIRS:
            errors.append(f"Non-canonical directory in evals/: evals/{child.name}/")

    for md_rel in ("evals/README.md", "evals/LATEST.md"):
        md_path = root / md_rel
        if not md_path.is_file():
            errors.append(f"Missing {md_rel}")
        else:
            md_content = md_path.read_text(encoding="utf-8")
            _validate_markdown_links(root, md_rel, md_content, errors)
            if _LEAK_RE.search(md_content):
                errors.append(f"Local path leaked: {md_rel}")

    matrix_path = root / "evals" / "matrix.json"
    if not matrix_path.is_file():
        errors.append("Missing evals/matrix.json")
    else:
        try:
            matrix_data = json.loads(matrix_path.read_text(encoding="utf-8"))
            expected_version = identity.get("version")
            matrix_version = matrix_data.get("version") if isinstance(matrix_data, dict) else None
            suite_revision = matrix_data.get("suite_revision") if isinstance(matrix_data, dict) else None
            rows = matrix_data.get("rows") if isinstance(matrix_data, dict) else None
            if (
                not isinstance(matrix_data, dict)
                or matrix_data.get("schema") != 1
                or not isinstance(suite_revision, str)
                or not suite_revision.strip()
                or not isinstance(rows, list)
                or not rows
            ):
                errors.append("Malformed evals/matrix.json: requires schema 1, suite_revision, and non-empty rows")
            else:
                if matrix_version != expected_version:
                    errors.append(
                        f"evals/matrix.json version ({matrix_version!r}) must match plugin.json ({expected_version!r})"
                    )
                if suite_revision != expected_version:
                    errors.append(
                        f"evals/matrix.json suite_revision ({suite_revision!r}) "
                        f"must match plugin.json ({expected_version!r})"
                    )
                seen_keys: set[tuple[str, str, str, str]] = set()
                seen_harnesses: set[str] = set()
                malformed_row = False
                for row in rows:
                    if (
                        not isinstance(row, dict)
                        or not all(
                            isinstance(row.get(field), str) and str(row[field]).strip()
                            for field in ("suite", "harness", "platform", "config", "remaining")
                        )
                        or not isinstance(row.get("required"), bool)
                    ):
                        errors.append("Malformed row in evals/matrix.json")
                        malformed_row = True
                        break
                    row_key = (row["suite"], row["harness"], row["platform"], row["config"])
                    if row_key in seen_keys:
                        errors.append(f"Duplicate row key in evals/matrix.json: {row_key}")
                    seen_keys.add(row_key)
                    seen_harnesses.add(str(row["harness"]))
                if not malformed_row and (len(rows) != 11 or len(seen_harnesses) != 11 or len(seen_keys) != 11):
                    errors.append(
                        f"evals/matrix.json must declare 11 unique host rows "
                        f"(found {len(rows)} rows, {len(seen_harnesses)} unique hosts)"
                    )
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid evals/matrix.json: {exc}")

    _validate_waza_manifest(root, "evals/waza/skills/daily-tasks/eval.yaml", errors)
    _validate_waza_manifest(root, "evals/waza/skills/daily-tasks/behavior.yaml", errors)


def _validate_license_and_host_metadata(
    root: Path,
    identity: dict[str, object],
    pyproject: dict[str, object],
    errors: list[str],
) -> None:
    license_path = root / "LICENSE"
    if not license_path.is_file():
        errors.append("Missing LICENSE at repo_root")
    else:
        license_text = license_path.read_text(encoding="utf-8")
        if "Apache License" not in license_text or "Version 2.0" not in license_text:
            errors.append("LICENSE at repo_root must contain Apache License, Version 2.0")

    project_table = pyproject.get("project")
    pyproject_license = project_table.get("license") if isinstance(project_table, dict) else None
    if identity.get("license") != "Apache-2.0" or pyproject_license != "Apache-2.0":
        errors.append("License mismatch: plugin.json and pyproject.toml must both declare Apache-2.0")

    synced_fields = ("name", "version", "description", "author", "homepage", "repository", "license", "keywords")
    for host_rel in (".claude-plugin/plugin.json", ".codex-plugin/plugin.json", ".cursor-plugin/plugin.json"):
        host_path = root / host_rel
        if not host_path.is_file():
            errors.append(f"Missing {host_rel} manifest")
            continue
        try:
            host_data = json.loads(host_path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid {host_rel}: {exc}")
            continue
        if not isinstance(host_data, dict) or any(
            host_data.get(field) != identity.get(field) for field in synced_fields
        ):
            errors.append(
                f"Metadata drift in {host_rel}: must match plugin.json "
                "name, version, description, author, homepage, repository, license, and keywords"
            )


def validate_repository(root: Path = ROOT) -> list[str]:
    """Validate repo layout, skills, docs lockdown, relative links, harness adapters, evals, and version parity."""
    errors: list[str] = []
    is_assembled = (root / "assembly.json").is_file()

    _validate_root_layout_and_gitattributes(root, is_assembled, errors)
    _validate_docs(root, is_assembled, errors)
    _validate_test_isolation(root, errors)
    names = _validate_skills(root, errors)
    _validate_retired_runtime_tokens(root, errors)

    identity = json.loads((root / "plugin.json").read_text(encoding="utf-8"))
    if identity.get("$schema") != "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json":
        errors.append("Missing or unsupported Agent Plugins v1 $schema in plugin.json")
    pyproject = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    pyproject_version = pyproject.get("project", {}).get("version")
    if identity.get("version") != pyproject_version or len(names) != 1:
        errors.append("Version or skill inventory mismatch")

    _validate_license_and_host_metadata(root, identity, pyproject, errors)

    readme_path = root / "README.md"
    if readme_path.is_file():
        readme_text = readme_path.read_text(encoding="utf-8")
        version_match = re.search(r"Version\s+\*\*([0-9]+\.[0-9]+\.[0-9]+)\*\*", readme_text)
        if version_match is None or version_match.group(1) != identity.get("version"):
            errors.append("README.md version mismatch")
        _validate_markdown_links(root, "README.md", readme_text, errors)
        if _LEAK_RE.search(readme_text):
            errors.append("Local path leaked: README.md")

    changelog_path = root / "CHANGELOG.md"
    if changelog_path.is_file():
        changelog_text = changelog_path.read_text(encoding="utf-8")
        _validate_markdown_links(root, "CHANGELOG.md", changelog_text, errors)
        if _LEAK_RE.search(changelog_text):
            errors.append("Local path leaked: CHANGELOG.md")

    hermes_adapter = root / "harness-adapters" / "hermes" / "plugin.py"
    if not hermes_adapter.is_file():
        errors.append("Missing harness-adapters/hermes/plugin.py")
    if (root / "harness-adapters" / "hermes" / "__init__.py").exists():
        errors.append(
            "Retired harness-adapters/hermes/__init__.py must not exist; use harness-adapters/hermes/plugin.py"
        )

    tessl_path = root / ".tessl-plugin" / "plugin.json"
    if not tessl_path.is_file():
        errors.append("Missing .tessl-plugin/plugin.json manifest")
    else:
        try:
            tessl_data = json.loads(tessl_path.read_text(encoding="utf-8"))
            expected_tessl = {
                "name": f"nyssa-ai/{identity.get('name')}",
                "version": identity.get("version"),
                "description": identity.get("description"),
                "private": True,
                "skills": "./skills",
                "mcpServers": ".mcp.json",
            }
            if tessl_data != expected_tessl:
                errors.append("Malformed .tessl-plugin/plugin.json manifest")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid .tessl-plugin/plugin.json: {exc}")

    gemini_path = root / "gemini-extension.json"
    if not gemini_path.is_file():
        errors.append("Missing gemini-extension.json manifest")
    else:
        try:
            gemini_data = json.loads(gemini_path.read_text(encoding="utf-8"))
            if isinstance(gemini_data, dict) and "contextFileName" in gemini_data:
                errors.append("gemini-extension.json must not include contextFileName")
            expected_gemini = {
                "name": identity.get("name"),
                "version": identity.get("version"),
                "description": identity.get("description"),
            }
            if gemini_data != expected_gemini:
                errors.append("Malformed gemini-extension.json manifest")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid gemini-extension.json: {exc}")

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
                or server_cfg.get("command") != "uv"
                or server_cfg.get("args")
                != [
                    "run",
                    "--no-project",
                    "python",
                    "${CLAUDE_PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py",
                ]
            ):
                errors.append("Malformed .mcp.json: daily-tasks server requires uv cross-platform launcher args")
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
                or portable_server_cfg.get("command") != "uv"
                or portable_server_cfg.get("args")
                != [
                    "run",
                    "--no-project",
                    "python",
                    "${PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py",
                ]
            ):
                errors.append("Malformed mcp.json: requires Agent Plugins v1 $schema and uv stdio daily-tasks server")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid mcp.json: {exc}")

    agy_mcp_path = root / "mcp_config.json"
    if not agy_mcp_path.exists():
        errors.append("Missing mcp_config.json Antigravity manifest")
    else:
        try:
            agy_raw = agy_mcp_path.read_text(encoding="utf-8")
            if "${PLUGIN_DATA}" in agy_raw:
                errors.append("Retired ${PLUGIN_DATA} placeholder must not appear in mcp_config.json")
            agy_mcp_data = json.loads(agy_raw)
            agy_servers = agy_mcp_data.get("mcpServers") if isinstance(agy_mcp_data, dict) else None
            agy_server_cfg = agy_servers.get("daily-tasks") if isinstance(agy_servers, dict) else None
            agy_args = agy_server_cfg.get("args") if isinstance(agy_server_cfg, dict) else None
            if (
                not isinstance(agy_mcp_data, dict)
                or set(agy_mcp_data) != {"mcpServers"}
                or not isinstance(agy_server_cfg, dict)
                or agy_server_cfg.get("command") != "uv"
                or not isinstance(agy_args, list)
                or len(agy_args) != 5
                or agy_args[:4] != ["run", "--no-project", "python", "-c"]
                or not isinstance(agy_args[4], str)
                or "runpy.run_path" not in agy_args[4]
                or "DAILY_TASKS_PLUGIN_ROOT" not in agy_args[4]
            ):
                errors.append("Malformed mcp_config.json: requires uv python -c bootstrapper for daily-tasks")
        except (OSError, ValueError) as exc:
            errors.append(f"Invalid mcp_config.json: {exc}")

    if not is_assembled:
        _validate_evals(root, identity, errors)

    return errors


def validate() -> int:
    """Run repository validation checks and report results."""
    errors = validate_repository()
    if errors:
        print("\n".join(errors), file=sys.stderr)
        return 1
    print(
        "Validated 1 skill, workflows, docs lockdown, relative links, path hygiene, "
        "harness adapters, evals, and version parity"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(validate())
