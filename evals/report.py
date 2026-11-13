"""Responsibility: Generate, check, summarize, and gate plugin evaluation evidence and LATEST.md.
Public interface:
+-- EVALS
+-- ROOT
+-- candidate_sha256()
+-- code_test_summary()
+-- main(argv)
+-- render()
+-- row_statuses()
+-- source_inventory()
+-- suite_sha256(suite)
+-- summary(run_code_tests)
`-- waza_summary(current)
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any, TypedDict

import yaml  # type: ignore[import-untyped]

ROOT = Path(__file__).resolve().parents[1]
EVALS = ROOT / "evals"
EXCLUDED = frozenset(
    {
        "reports",
        ".temp",
        ".git",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        ".ruff_cache",
        ".venv",
        "venv",
        "results",
        "attempts",
        "evidence",
        ".nyssa-ai",
        ".nyssaai",
        ".nyssa",
    }
)
_TEXT_SUFFIXES = frozenset(
    {
        ".md",
        ".py",
        ".json",
        ".yaml",
        ".yml",
        ".txt",
        ".toml",
        ".lock",
        ".mjs",
        ".js",
        ".sh",
        ".ps1",
    }
)
_TEXT_FILENAMES = frozenset({"LICENSE", ".gitattributes", ".gitignore"})


class RowStatus(TypedDict):
    row: dict[str, Any]
    data: dict[str, Any] | None
    result_link: str
    outcome: str
    freshness: str
    attempt_text: str
    passing: bool


def evidence_root() -> Path:
    """Resolve the active evaluation evidence directory."""
    if (EVALS / "evidence").exists():
        return EVALS / "evidence"
    return ROOT / ".temp" / "evals" / "evidence"


def read_json(path: Path) -> dict[str, Any]:
    """Read a UTF-8 JSON object from disk."""
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return loaded


def _load_yaml(path: Path) -> object:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _normalize_text_bytes(raw: bytes) -> bytes:
    return raw.replace(b"\r\n", b"\n").replace(b"\r", b"\n")


def matches_sha256(raw: bytes, expected: str | None) -> bool:
    """Check whether raw bytes match expected SHA-256 across LF/CRLF line endings."""
    if not expected:
        return False
    lf = raw.replace(b"\r\n", b"\n")
    crlf = lf.replace(b"\n", b"\r\n")
    return any(hashlib.sha256(candidate).hexdigest() == expected for candidate in (raw, lf, crlf))


def source_inventory() -> dict[str, str]:
    """Freeze the declared behavior, assembly, and suite inputs, excluding ephemeral outputs."""
    paths: list[Path] = []
    for top in (
        "skills",
        "src",
        "scripts",
        "harness-adapters",
        "docs",
        ".claude-plugin",
        ".codex-plugin",
        ".cursor-plugin",
        ".tessl-plugin",
        ".github",
        "test",
        "evals",
    ):
        top_dir = ROOT / top
        if top_dir.exists():
            paths.extend(top_dir.rglob("*"))
    paths.extend(
        ROOT / name
        for name in (
            "plugin.json",
            "gemini-extension.json",
            ".mcp.json",
            "mcp.json",
            "mcp_config.json",
            "pyproject.toml",
            "uv.lock",
            "AGENTS.md",
            "CLAUDE.md",
            "GEMINI.md",
            "README.md",
            "LICENSE",
            ".gitattributes",
            ".gitignore",
        )
    )
    result: dict[str, str] = {}
    for path in sorted(set(paths)):
        if not path.is_file() or path.is_symlink():
            continue
        rel_parts = path.relative_to(ROOT).parts
        if any(part in EXCLUDED for part in rel_parts) or path.name == "LATEST.md":
            continue
        content = path.read_bytes()
        if path.suffix.lower() in _TEXT_SUFFIXES or path.name in _TEXT_FILENAMES:
            content = _normalize_text_bytes(content)
        result[path.relative_to(ROOT).as_posix()] = hashlib.sha256(content).hexdigest()
    return result


def candidate_sha256() -> str:
    """Compute the deterministic candidate SHA-256 across the tracked source inventory."""
    data = json.dumps(source_inventory(), sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(data).hexdigest()


def key(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Extract the unique four-part coverage matrix key from a row."""
    return (
        str(row["suite"]),
        str(row["harness"]),
        str(row["platform"]),
        str(row["config"]),
    )


def suite_sha256(suite: str) -> str:
    """Compute a deterministic digest of the repository-owned suite definition."""
    if suite != "daily-tasks":
        raise ValueError(f"Unknown suite: {suite}")
    suite_dir = EVALS / "waza" / "skills" / "daily-tasks"
    if not suite_dir.is_dir():
        raise ValueError(f"Missing suite directory: {suite_dir}")
    digest = hashlib.sha256()
    for path in sorted(suite_dir.rglob("*")):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(suite_dir)
        if any(part in EXCLUDED for part in rel.parts):
            continue
        content = path.read_bytes()
        if path.suffix.lower() in _TEXT_SUFFIXES or path.name in _TEXT_FILENAMES:
            content = _normalize_text_bytes(content)
        digest.update(rel.as_posix().encode("utf-8") + b"\0" + content + b"\0")
    return digest.hexdigest()


def records(
    kind: str,
    matrix_keys: set[tuple[str, str, str, str]],
) -> list[tuple[Path, dict[str, Any]]]:
    """Load result or attempt metadata records matching declared matrix keys."""
    ev = evidence_root()
    root = ev / kind if (ev / kind).exists() else EVALS / kind
    output: list[tuple[Path, dict[str, Any]]] = []
    if root.exists():
        for path in sorted(root.glob("*/metadata.json")):
            data = read_json(path)
            raw_key = data.get("key")
            if (
                not isinstance(raw_key, list)
                or len(raw_key) != 4
                or (str(raw_key[0]), str(raw_key[1]), str(raw_key[2]), str(raw_key[3])) not in matrix_keys
            ):
                raise ValueError(f"Undeclared evaluation row: {path}")
            output.append((path, data))
    return output


def latest(items: list[tuple[Path, dict[str, Any]]]) -> tuple[Path, dict[str, Any]] | None:
    """Return the most recently completed record from a list of candidate records."""
    return max(
        items,
        key=lambda item: (str(item[1]["completed_at"]), item[0].parent.name),
        default=None,
    )


def valid_completed(path: Path, data: dict[str, Any]) -> None:
    """Validate a completed native-host evaluation receipt and its evidence archive."""
    if data.get("state") != "completed" or data.get("verified") is not True:
        raise ValueError(f"Result is not completed and verified: {path}")
    score = data.get("score")
    if data.get("outcome") not in ("Pass", "Fail") or not isinstance(score, (int, float)) or isinstance(score, bool):
        raise ValueError(f"Result has no real scored outcome: {path}")
    if not 0 <= float(score) <= 100:
        raise ValueError(f"Result score out of range: {path}")
    for field in (
        "host_version",
        "model",
        "artifact",
        "artifact_sha256",
        "suite_sha256",
        "scoring_method",
        "reviewer",
        "review_method",
        "critical_failures",
        "case_outcomes",
    ):
        if field not in data or data[field] in (None, ""):
            raise ValueError(f"Result lacks {field}: {path}")
    row_key = data["key"]
    if (
        data.get("host") != row_key[1]
        or data.get("platform") != row_key[2]
        or data.get("config") != row_key[3]
    ):
        raise ValueError(f"Result host/platform/config disagrees with row: {path}")
    if not isinstance(data["critical_failures"], list) or not isinstance(data["case_outcomes"], list):
        raise ValueError(f"Result case or failure record has wrong shape: {path}")
    if not data["case_outcomes"]:
        raise ValueError(f"Result lacks case outcomes: {path}")
    artifact_name = str(data["artifact"])
    if Path(artifact_name).is_absolute() or ".." in Path(artifact_name).parts:
        raise ValueError(f"Unsafe artifact path: {path}")
    artifact = path.parent / artifact_name
    if not artifact.is_file() or hashlib.sha256(artifact.read_bytes()).hexdigest() != data["artifact_sha256"]:
        raise ValueError(f"Result artifact missing or hash mismatch: {path}")
    if not zipfile.is_zipfile(artifact):
        raise ValueError(f"Result artifact is not an inspectable ZIP: {path}")
    with zipfile.ZipFile(artifact) as archive:
        names = archive.namelist()
        if not names or any(name.startswith("/") or ".." in Path(name).parts for name in names):
            raise ValueError(f"Result artifact has invalid paths: {path}")
    if data.get("reviewer_independent") is not True:
        raise ValueError(f"Result lacks independent review: {path}")
    if data["critical_failures"] and data["outcome"] == "Pass":
        raise ValueError(f"Critical failure cannot pass release: {path}")
    matrix = read_json(EVALS / "matrix.json")
    if data.get("suite_revision") != matrix["suite_revision"]:
        raise ValueError(f"Unknown suite revision: {path}")
    if data.get("suite_sha256") != suite_sha256(str(row_key[0])):
        raise ValueError(f"Suite source hash mismatch: {path}")
    evidence_name = str(data.get("evidence", ""))
    if not evidence_name or Path(evidence_name).is_absolute() or ".." in Path(evidence_name).parts:
        raise ValueError(f"Unsafe or missing result evidence path: {path}")
    evidence = path.parent / evidence_name
    if not evidence.is_file() or not matches_sha256(evidence.read_bytes(), data.get("evidence_sha256")):
        raise ValueError(f"Result evidence missing or hash mismatch: {path}")
    trace_path = path.parent / "host-trace.json"
    if not trace_path.is_file():
        raise ValueError(f"Result lacks host invocation trace: {path}")
    trace = read_json(trace_path)
    invocations = trace.get("invocations")
    if trace.get("host") != data["host"] or not isinstance(invocations, list) or not invocations:
        raise ValueError(f"Result has no structured host invocation evidence: {path}")
    datetime.fromisoformat(str(data["completed_at"]).replace("Z", "+00:00"))


def valid_attempt(path: Path, data: dict[str, Any]) -> None:
    """Validate an incomplete, aborted, or unverified evaluation attempt record."""
    if data.get("state") not in ("incomplete", "aborted", "unverified"):
        raise ValueError(f"Attempt has invalid state: {path}")
    for field in ("started_at", "completed_at", "stage", "diagnostic", "next_check", "candidate_sha256"):
        if not data.get(field):
            raise ValueError(f"Attempt lacks {field}: {path}")
    datetime.fromisoformat(str(data["completed_at"]).replace("Z", "+00:00"))


def is_current(data: dict[str, Any], current: str, revision: str) -> bool:
    """Check whether a completed result matches the current candidate and suite digest."""
    return (
        data.get("candidate_sha256") == current
        and data.get("suite_revision") == revision
        and data.get("suite_sha256") == suite_sha256(str(data["key"][0]))
    )


def _row_key_from_record(data: dict[str, Any]) -> tuple[str, str, str, str]:
    raw = data["key"]
    return (str(raw[0]), str(raw[1]), str(raw[2]), str(raw[3]))


def row_statuses() -> tuple[dict[str, Any], str, list[RowStatus]]:
    """Select the displayed result, freshness, and attempt status for every matrix row."""
    matrix = read_json(EVALS / "matrix.json")
    rows = matrix["rows"]
    if not isinstance(rows, list) or len({key(row) for row in rows}) != len(rows):
        raise ValueError("Coverage matrix contains invalid or duplicate keys")
    matrix_keys = {key(row) for row in rows}
    results = records("results", matrix_keys)
    attempts = records("attempts", matrix_keys)
    for path, data in results:
        valid_completed(path, data)
    for path, data in attempts:
        valid_attempt(path, data)
    current = candidate_sha256()
    revision = str(matrix["suite_revision"])
    statuses: list[RowStatus] = []
    for row in rows:
        row_k = key(row)
        matching = [(p, d) for p, d in results if _row_key_from_record(d) == row_k]
        selected = latest([(p, d) for p, d in matching if is_current(d, current, revision)]) or latest(matching)
        selected_attempt = latest([(p, d) for p, d in attempts if _row_key_from_record(d) == row_k])
        if selected is not None:
            sel_path, sel_data = selected
            result_link = f"`{sel_path.parent.name}`"
            outcome = f"{sel_data['outcome']} / {sel_data['score']}/100"
            freshness = "Current" if is_current(sel_data, current, revision) else "Stale"
            record_data: dict[str, Any] | None = sel_data
        else:
            result_link, outcome, freshness = "Not run", "Score unavailable", "No result"
            record_data = None
        attempt_text = str(row["remaining"])
        if selected_attempt is not None and (
            selected is None or str(selected_attempt[1]["completed_at"]) > str(selected[1]["completed_at"])
        ):
            att_path, attempt = selected_attempt
            attempt_link = f"`{att_path.parent.name}`"
            if attempt["candidate_sha256"] == current:
                attempt_text = f"{attempt_link}: {attempt['state']}; {attempt['next_check']}"
            else:
                attempt_text = f"{attempt_link}: {attempt['state']} on an earlier candidate; {row['remaining']}"
        statuses.append(
            {
                "row": row,
                "data": record_data,
                "result_link": result_link,
                "outcome": outcome,
                "freshness": freshness,
                "attempt_text": attempt_text,
                "passing": bool(record_data and record_data["outcome"] == "Pass" and freshness == "Current"),
            }
        )
    return matrix, current, statuses


def render() -> tuple[str, bool]:
    """Render `evals/LATEST.md` and compute overall release readiness."""
    matrix, current, statuses = row_statuses()
    lines = [
        "# Latest plugin evaluation",
        "",
        (
            "Generated from [matrix.json](matrix.json), "
            "[waza/skills/daily-tasks/eval.yaml](waza/skills/daily-tasks/eval.yaml), "
            "[waza/skills/daily-tasks/behavior.yaml](waza/skills/daily-tasks/behavior.yaml), "
            "and verified `.temp/evals/evidence/` receipts by `uv run python evals/report.py generate`."
        ),
        f"Candidate SHA-256: `{current}`. Suite revision: `{matrix['suite_revision']}`.",
        "",
        "A missing or failing required row blocks release. A consistent report does not imply release readiness.",
        "",
        (
            "Offline Waza trigger and behavioral definitions live in `evals/waza/skills/daily-tasks/` "
            "(see [README.md](README.md) for workflow instructions)."
        ),
        "",
        (
            "| Suite | Harness | Platform | Configuration | Required | Latest completed result "
            "| Outcome / score | Freshness | Newer attempt / next check |"
        ),
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    ready = True
    for status in statuses:
        row = status["row"]
        if row["required"] and not status["passing"]:
            ready = False
        cells = [
            *key(row),
            "Yes" if row["required"] else "No",
            status["result_link"],
            status["outcome"],
            status["freshness"],
            status["attempt_text"],
        ]
        lines.append("| " + " | ".join(str(c).replace("|", "\\|").replace("\n", " ") for c in cells) + " |")
    acceptance = "Pass" if ready else "Fail — required evidence missing, stale, or failing"
    lines += ["", f"Release acceptance: **{acceptance}**.", ""]
    return "\n".join(lines), ready


def _clean_checkout_report_matches(existing: str, rendered_empty: str) -> bool:
    """Verify LATEST.md identity and row parity on clean checkouts without .temp/evals/evidence/."""
    existing_lines = existing.splitlines()
    rendered_lines = rendered_empty.splitlines()
    if len(existing_lines) != len(rendered_lines):
        return False
    if existing_lines[:11] != rendered_lines[:11] or existing_lines[-2:] != rendered_lines[-2:]:
        return False
    if "Release acceptance: **Fail" not in existing_lines[-1]:
        return False
    for ex_row, ren_row in zip(existing_lines[11:-2], rendered_lines[11:-2], strict=True):
        ex_cells = [c.strip() for c in ex_row.strip("| ").split("|")]
        ren_cells = [c.strip() for c in ren_row.strip("| ").split("|")]
        if len(ex_cells) != 9 or len(ren_cells) != 9:
            return False
        if ex_cells[:5] != ren_cells[:5]:
            return False
        if ex_cells[5] != "Not run" and ex_cells[7] != "Stale":
            return False
    return True


def _extract_test_cases(loaded: object, task_file: Path) -> list[dict[str, Any]]:
    if isinstance(loaded, dict):
        return [loaded]
    if isinstance(loaded, list) and all(isinstance(item, dict) for item in loaded):
        return list(loaded)
    raise ValueError(f"Expected single TestCase mapping or list of mappings in {task_file}")


def waza_summary(current: str) -> list[dict[str, Any]]:
    """List registered Waza tasks across eval.yaml and behavior.yaml manifests."""
    suites: list[dict[str, Any]] = []
    waza_skills_dir = EVALS / "waza" / "skills"
    if not waza_skills_dir.is_dir():
        return suites
    for skill_dir in sorted(p for p in waza_skills_dir.iterdir() if p.is_dir()):
        for manifest_name in ("eval.yaml", "behavior.yaml"):
            manifest_file = skill_dir / manifest_name
            if not manifest_file.is_file():
                continue
            raw_def = _load_yaml(manifest_file)
            definition = raw_def if isinstance(raw_def, dict) else {}
            task_patterns = definition.get("tasks")
            patterns = task_patterns if isinstance(task_patterns, list) else []
            matched_files: list[Path] = []
            for pattern in patterns:
                if isinstance(pattern, str):
                    for candidate in sorted(skill_dir.glob(pattern)):
                        if candidate.is_file() and candidate not in matched_files:
                            matched_files.append(candidate)
            tasks: list[dict[str, Any]] = []
            for task_file in matched_files:
                for task in _extract_test_cases(_load_yaml(task_file), task_file):
                    graders = task.get("graders")
                    grader_list = graders if isinstance(graders, list) else []
                    grader_names = ", ".join(
                        str(g.get("name", g.get("type", ""))) for g in grader_list if isinstance(g, dict)
                    )
                    tasks.append(
                        {
                            "id": str(task["id"]),
                            "name": str(task.get("name", "")),
                            "file": task_file.relative_to(ROOT).as_posix(),
                            "tags": list(task.get("tags", [])) if isinstance(task.get("tags"), list) else [],
                            "grader": grader_names,
                        }
                    )
            outcomes: dict[str, str] = {}
            receipt_used: str | None = None
            receipt_dirs = [
                skill_dir / "results",
                evidence_root() / "waza" / skill_dir.name,
            ]
            for receipt_dir in receipt_dirs:
                if not receipt_dir.is_dir():
                    continue
                for receipt in sorted(receipt_dir.glob("*.json")):
                    data = read_json(receipt)
                    if (
                        data.get("candidate_sha256") == current
                        and data.get("suite") in (None, definition.get("name", skill_dir.name))
                        and data.get("executor") not in (None, "", "mock")
                        and isinstance(data.get("tasks"), list)
                    ):
                        outcomes = {
                            str(item["id"]): str(item["outcome"])
                            for item in data["tasks"]
                            if isinstance(item, dict) and item.get("outcome") in ("Pass", "Fail") and "id" in item
                        }
                        receipt_used = f"`{receipt.stem}`"
            for task in tasks:
                task["outcome"] = outcomes.get(task["id"], "Not run")
            config_obj = definition.get("config")
            executor = config_obj.get("executor") if isinstance(config_obj, dict) else None
            suites.append(
                {
                    "suite": str(definition.get("name", skill_dir.name)),
                    "manifest": manifest_file.relative_to(ROOT).as_posix(),
                    "executor": executor,
                    "receipt": receipt_used,
                    "tasks": tasks,
                }
            )
    return suites


def code_test_summary() -> dict[str, int]:
    """Run pytest across unit and use-case suites and return deterministic counts."""
    (ROOT / ".temp").mkdir(exist_ok=True)
    completed = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "--tb=no", "--no-header"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        check=False,
    )
    output = completed.stdout + "\n" + completed.stderr
    passed = sum(int(n) for n in re.findall(r"(\d+)\s+passed\b", output))
    failed = sum(int(n) for n in re.findall(r"(\d+)\s+failed\b", output))
    errors = sum(int(n) for n in re.findall(r"(\d+)\s+errors?\b", output))
    failing = failed + errors
    total = passed + failing
    return {
        "total": total,
        "passing": passed,
        "failing": failing,
        "exit_code": completed.returncode,
    }


def _counts(outcomes: list[str]) -> dict[str, int | float]:
    total = len(outcomes)
    passing = outcomes.count("Pass")
    failing = outcomes.count("Fail")
    return {
        "total": total,
        "passing": passing,
        "failing": failing,
        "not_run": total - passing - failing,
        "pass_rate": round(100 * passing / total, 1) if total else 0.0,
    }


def summary(run_code_tests: bool = True) -> dict[str, Any]:
    """Return deterministic evaluation counts; Not run is never counted as passing."""
    matrix, current, statuses = row_statuses()
    waza = waza_summary(current)
    waza_tasks = [task for suite in waza for task in suite["tasks"]]
    suites: dict[str, dict[str, int | float]] = {
        "waza": _counts([str(task["outcome"]) for task in waza_tasks]),
        "host_matrix": _counts(
            [
                "Pass" if s["passing"] else ("Fail" if s["data"] and s["freshness"] == "Current" else "Not run")
                for s in statuses
            ]
        ),
    }
    if run_code_tests:
        code = code_test_summary()
        suites["code_tests"] = {
            **code,
            "not_run": 0,
            "pass_rate": round(100 * code["passing"] / code["total"], 1) if code["total"] else 0.0,
        }
    total = sum(int(s["total"]) for s in suites.values())
    passing = sum(int(s["passing"]) for s in suites.values())
    return {
        "candidate_sha256": current,
        "suite_revision": matrix["suite_revision"],
        "release_ready": all(s["passing"] for s in statuses if s["row"]["required"]),
        "suites": suites,
        "overall": {
            "total": total,
            "passing": passing,
            "pass_rate": round(100 * passing / total, 1) if total else 0.0,
        },
        "waza": waza,
        "matrix": [
            {
                "harness": s["row"]["harness"],
                "required": s["row"]["required"],
                "outcome": s["outcome"],
                "freshness": s["freshness"],
            }
            for s in statuses
        ],
    }


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for `evals/report.py`."""
    parser = argparse.ArgumentParser(description="Generate, check, summarize, and gate plugin evaluation evidence.")
    parser.add_argument("command", choices=("generate", "check", "release", "hash", "summary"))
    parser.add_argument("--no-code-tests", action="store_true", help="summary only: skip running the pytest suite")
    args = parser.parse_args(argv)
    if args.command == "hash":
        print(candidate_sha256())
        return 0
    if args.command == "summary":
        print(json.dumps(summary(run_code_tests=not args.no_code_tests), indent=2))
        return 0
    report, ready = render()
    path = EVALS / "LATEST.md"
    if args.command == "generate":
        path.write_text(report, encoding="utf-8", newline="\n")
        print(path)
        return 0
    if not path.exists():
        print("LATEST.md differs from evidence; run generate and inspect the diff", file=sys.stderr)
        return 1
    existing = path.read_text(encoding="utf-8").replace("\r\n", "\n")
    consistent = existing == report or (
        args.command == "check" and not evidence_root().exists() and _clean_checkout_report_matches(existing, report)
    )
    if not consistent:
        print("LATEST.md differs from evidence; run generate and inspect the diff", file=sys.stderr)
        return 1
    if args.command == "release" and not ready:
        print("Release acceptance failed: required rows lack current passing evidence", file=sys.stderr)
        return 1
    print("Report consistent" + ("; release ready" if ready else "; release incomplete"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
