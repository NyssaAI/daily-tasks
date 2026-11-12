"""Responsibility: Inspect, seed, and track SHA-256 baselines for vault Markdown templates.
Public interface:
`-- TemplateSynchronizer
    +-- discover_existing(vault_root, templates_dir)
    +-- new(clock, plugin_version, assets_dir)
    +-- sync(vault_root, resolved_tpl_dir, tpl_rel_path, updates_path, existing_pointers)
    `-- validate_baseline(vault_root, user_home, updates_path, templates_map)
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from datetime import datetime
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.records.atomic_write import atomic_write

_DEFAULT_ASSETS_DIR: Final = Path(__file__).resolve().parents[3] / "skills" / "daily-tasks" / "assets"

_TEMPLATE_SPECS: Final[tuple[tuple[str, str, tuple[str, ...], str], ...]] = (
    ("projectIndex", "project-index.md", ("daily-tasks-project-index.md", "project-index.md"), "project-index.md"),
    ("dailyPlan", "daily-plan.md", ("daily-tasks-daily-plan.md", "daily-plan.md"), "daily-plan.md"),
    ("milestone", "milestone.md", ("daily-tasks-milestone.md", "milestone.md"), "milestone.md"),
    ("task", "task.md", ("daily-tasks-task.md", "task.md"), "task.md"),
    (
        "planDayReview",
        "plan-day-select-tasks-screen.md",
        (
            "daily-tasks-plan-day-select-tasks-screen.md",
            "plan-day-select-tasks-screen.md",
            "daily-tasks-plan-day-review.md",
            "plan-day-review.md",
        ),
        "plan-day-review.md",
    ),
)
_AUXILIARY_ASSETS: Final[tuple[tuple[str, tuple[str, ...], str], ...]] = (
    ("blocker.md", ("daily-tasks-blocker.md", "blocker.md"), "blocker.md"),
)


def _sha256_text(content: str) -> str:
    normalized = content.replace("\r\n", "\n")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _resolve_pointer(vault_root: Path, user_home: Path, pointer: str) -> Path | None:
    trimmed = pointer.strip()
    if not trimmed:
        return None
    if trimmed.startswith("./"):
        rel = Path(trimmed[2:])
        if ".." in rel.parts:
            return None
        resolved = (vault_root / rel).resolve()
        return resolved if resolved.is_relative_to(vault_root) else None
    if trimmed.startswith("~/"):
        rel = Path(trimmed[2:])
        if ".." in rel.parts:
            return None
        return (user_home / rel).resolve()
    candidate = Path(trimmed)
    return candidate.resolve() if candidate.is_absolute() else (vault_root / candidate).resolve()


def _read_updates_json(path: Path) -> Result[dict[str, JsonValue] | None]:
    if path.is_symlink():
        return fail(f"Template baseline file at {path.as_posix()} must not be a symlink.", ErrorCategory.VALIDATION)
    try:
        raw_text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ok(None)
    except OSError as exc:
        return fail(f"Unable to read {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    try:
        parsed = json.loads(raw_text)
    except ValueError as exc:
        return fail(f"Malformed JSON in {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
    if not isinstance(parsed, dict):
        return fail(
            f"Template baseline file at {path.as_posix()} must contain a JSON object.", ErrorCategory.VALIDATION
        )
    return ok(parsed)


@final
class TemplateSynchronizer:
    """Seed missing Markdown templates into a vault and store SHA-256 baselines in `config_dir`."""

    def __init__(
        self,
        clock: Callable[[], datetime],
        plugin_version: str = "0.11.2",
        assets_dir: Path | None = None,
    ) -> None:
        """Store UTC clock, plugin version, and bundled template assets directory."""
        self._clock = clock
        self._plugin_version = plugin_version
        self._assets_dir = assets_dir if assets_dir is not None else _DEFAULT_ASSETS_DIR

    def discover_existing(self, vault_root: Path, templates_dir: str) -> dict[str, str]:
        """Return existing template pointers discovered inside `<vault_root>/<templates_dir>`."""
        rel = templates_dir[2:] if templates_dir.startswith("./") else templates_dir
        candidate_dir = vault_root / Path(rel)
        discovered: dict[str, str] = {}
        if not candidate_dir.is_dir():
            return discovered
        rel_prefix = templates_dir.rstrip("/")
        for kind, _, existing_names, _ in _TEMPLATE_SPECS:
            for fname in existing_names:
                if (candidate_dir / fname).is_file():
                    discovered[kind] = f"{rel_prefix}/{fname}"
                    break
        return discovered

    def validate_baseline(
        self,
        vault_root: Path,
        user_home: Path,
        updates_path: Path,
        templates_map: JsonValue,
    ) -> Result[bool]:
        """Return True when `updates_path` exists and every registered template pointer resolves to a file."""
        updates_raw = _read_updates_json(updates_path)
        if not updates_raw.ok:
            return fail(updates_raw.message, updates_raw.category)
        if updates_raw.value is None or not isinstance(templates_map, dict):
            return ok(False)
        for kind, _, _, _ in _TEMPLATE_SPECS:
            pointer = templates_map.get(kind)
            if pointer is None:
                continue
            if not isinstance(pointer, str):
                return ok(False)
            target = _resolve_pointer(vault_root, user_home, pointer)
            if target is None or not target.is_file():
                return ok(False)
        return ok(True)

    def sync(
        self,
        vault_root: Path,
        resolved_tpl_dir: Path,
        tpl_rel_path: Path,
        updates_path: Path,
        existing_pointers: Mapping[str, JsonValue],
    ) -> Result[tuple[dict[str, JsonValue], list[str], list[str], Path]]:
        """Seed missing templates into `resolved_tpl_dir` without overwriting customized files, and save baselines."""
        if not self._assets_dir.is_dir():
            return fail(
                f"Bundled template assets directory is missing at {self._assets_dir.as_posix()}.",
                ErrorCategory.VALIDATION,
            )
        try:
            resolved_tpl_dir.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            return fail(
                f"Unable to create templates directory {resolved_tpl_dir.as_posix()}: {exc}", ErrorCategory.VALIDATION
            )

        updates_res = _read_updates_json(updates_path)
        if not updates_res.ok:
            return fail(updates_res.message, updates_res.category)
        existing_updates = updates_res.value if isinstance(updates_res.value, dict) else {}
        existing_policies = existing_updates.get("policies")
        policies: dict[str, JsonValue] = dict(existing_policies) if isinstance(existing_policies, dict) else {}
        existing_baselines = existing_updates.get("baselines")
        baselines: dict[str, JsonValue] = dict(existing_baselines) if isinstance(existing_baselines, dict) else {}

        registered: dict[str, JsonValue] = {}
        seeded: list[str] = []
        reused: list[str] = []
        now_iso = self._clock().strftime("%Y-%m-%dT%H:%M:%SZ")
        rel_prefix = f"./{tpl_rel_path.as_posix()}"

        for kind, asset_name, candidate_names, default_dest_name in _TEMPLATE_SPECS:
            asset_file = self._assets_dir / asset_name
            if not asset_file.is_file():
                return fail(f"Missing bundled template asset {asset_file.as_posix()}.", ErrorCategory.VALIDATION)
            bundled_text = asset_file.read_text(encoding="utf-8").replace("\r\n", "\n")
            policies.setdefault(kind, "ask")

            if kind in existing_pointers and existing_pointers[kind] is None:
                registered[kind] = None
                continue

            chosen_file: Path | None = None
            chosen_pointer: str | None = None
            existing_ptr = existing_pointers.get(kind)
            if isinstance(existing_ptr, str):
                resolved_existing = _resolve_pointer(vault_root, Path.home(), existing_ptr)
                if resolved_existing is not None and resolved_existing.is_file():
                    chosen_file = resolved_existing
                    chosen_pointer = existing_ptr

            if chosen_file is None:
                for cand in candidate_names:
                    cand_path = resolved_tpl_dir / cand
                    if cand_path.is_file():
                        chosen_file = cand_path
                        chosen_pointer = f"{rel_prefix}/{cand}"
                        break

            if chosen_file is None or chosen_pointer is None:
                dest_file = resolved_tpl_dir / default_dest_name
                if dest_file.exists() and dest_file.is_symlink():
                    return fail(
                        f"Refusing to write template through symlink {dest_file.as_posix()}.", ErrorCategory.VALIDATION
                    )
                dest_file.write_text(bundled_text, encoding="utf-8", newline="\n")
                chosen_file = dest_file
                chosen_pointer = f"{rel_prefix}/{default_dest_name}"
                seeded.append(chosen_file.as_posix())
            else:
                reused.append(chosen_file.as_posix())

            registered[kind] = chosen_pointer
            active_text = chosen_file.read_text(encoding="utf-8").replace("\r\n", "\n")
            vault_key = f"{vault_root.as_posix()}::{kind}"
            if vault_key not in baselines:
                baselines[vault_key] = {
                    "vault_root": vault_root.as_posix(),
                    "kind": kind,
                    "path": chosen_pointer,
                    "plugin_version": self._plugin_version,
                    "bundled_sha256": _sha256_text(bundled_text),
                    "active_sha256": _sha256_text(active_text),
                    "recorded_at": now_iso,
                }
            if kind not in baselines:
                baselines[kind] = baselines[vault_key]

        for aux_asset, aux_candidates, aux_default in _AUXILIARY_ASSETS:
            aux_src = self._assets_dir / aux_asset
            if aux_src.is_file() and not any((resolved_tpl_dir / name).is_file() for name in aux_candidates):
                aux_dest = resolved_tpl_dir / aux_default
                if not aux_dest.is_symlink():
                    aux_dest.write_text(
                        aux_src.read_text(encoding="utf-8").replace("\r\n", "\n"), encoding="utf-8", newline="\n"
                    )
                    seeded.append(aux_dest.as_posix())

        updates_doc: dict[str, JsonValue] = {
            **existing_updates,
            "schema_version": 1,
            "policies": policies,
            "baselines": baselines,
        }
        if updates_path.exists() and updates_path.is_symlink():
            return fail(f"Refusing to write through symlink at {updates_path.as_posix()}.", ErrorCategory.VALIDATION)
        try:
            encoded = (json.dumps(updates_doc, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
            atomic_write(updates_path, encoded)
        except OSError as exc:
            return fail(f"Unable to write {updates_path.as_posix()}: {exc}", ErrorCategory.VALIDATION)

        return ok((registered, seeded, reused, updates_path))
