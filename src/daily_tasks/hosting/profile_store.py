"""Responsibility: Read and write Schema Version 2 Daily Tasks config.json in user_home and repo_root.
Public interface:
+-- LEGACY_PROFILE_FILENAME
+-- ProfileStore
|   +-- home_root
|   +-- new(config_dir, repo_root)
|   +-- read_layered(vault_root)
|   +-- read_raw(path)
|   +-- read_strict_v2(path)
|   +-- repo_config_path
|   +-- repo_dir
|   +-- repo_profile_path
|   +-- templates_updates_path
|   +-- user_config_path
|   +-- user_dir
|   +-- user_profile_path
|   +-- write_user_config(payload)
|   `-- write_user_profile(payload)
`-- USER_CONFIG_FILENAME
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final, final

from nyssa_ai_result import ErrorCategory, Result, fail, ok
from pydantic import JsonValue

from daily_tasks.hosting.record_usage_event import extract_telemetry_enabled

USER_CONFIG_FILENAME: Final = "config.json"
LEGACY_PROFILE_FILENAME: Final = "profile.json"
_APP_SUBDIR: Final = Path(".nyssa-ai") / "daily-tasks"
_REQUIRED_SCHEMA_VERSION: Final = 2


def _is_schema_v2(value: JsonValue) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value == _REQUIRED_SCHEMA_VERSION


def _resolve_read_path(directory: Path) -> Path:
    canonical = directory / USER_CONFIG_FILENAME
    if canonical.is_symlink() or canonical.exists():
        return canonical
    legacy = directory / LEGACY_PROFILE_FILENAME
    if legacy.is_symlink() or legacy.exists():
        return legacy
    return canonical


def _merge_profile_layer(base: Mapping[str, JsonValue], overlay: Mapping[str, JsonValue]) -> dict[str, JsonValue]:
    merged: dict[str, JsonValue] = dict(base)
    for key, value in overlay.items():
        if key == "vaults":
            continue
        existing = merged.get(key)
        if isinstance(value, dict) and isinstance(existing, dict):
            merged[key] = {**existing, **value}
        else:
            merged[key] = value
    return merged


def _apply_vault_section(
    merged: dict[str, JsonValue],
    layer: Mapping[str, JsonValue],
    vault_posix: str,
) -> dict[str, JsonValue]:
    vaults_obj = layer.get("vaults")
    if not isinstance(vaults_obj, dict):
        return merged
    entry = vaults_obj.get(vault_posix)
    if not isinstance(entry, dict):
        return merged
    return _merge_profile_layer(merged, entry)


@final
class ProfileStore:
    """Layered Schema Version 2 `config.json` store across `user_home` and optional `repo_root`.

    Reads canonical `config.json` first, falling back read-only to legacy `profile.json` when `config.json`
    is absent. Always writes canonical `<user_dir>/config.json` and never reads or writes `<vault_root>/.nyssa-ai/`.
    """

    def __init__(self, config_dir: Path | None = None, repo_root: Path | None = None) -> None:
        """Bind `user_home` config directory (`~/.nyssa-ai/daily-tasks` by default) and optional `repo_root`."""
        if config_dir is not None:
            self._user_dir = config_dir.expanduser().resolve()
            if self._user_dir.name == "daily-tasks" and self._user_dir.parent.name == ".nyssa-ai":
                self._home_root = self._user_dir.parent.parent
            else:
                self._home_root = Path.home()
        else:
            self._home_root = Path.home()
            self._user_dir = (self._home_root / _APP_SUBDIR).resolve()
        self._repo_dir = (repo_root.expanduser().resolve() / _APP_SUBDIR).resolve() if repo_root is not None else None

    @property
    def user_dir(self) -> Path:
        """Resolved `user_home` configuration directory (`~/.nyssa-ai/daily-tasks`)."""
        return self._user_dir

    @property
    def repo_dir(self) -> Path | None:
        """Optional resolved `<repo_root>/.nyssa-ai/daily-tasks` configuration directory."""
        return self._repo_dir

    @property
    def home_root(self) -> Path:
        """Resolved user home root directory."""
        return self._home_root

    @property
    def user_config_path(self) -> Path:
        """Canonical path to `<user_dir>/config.json`."""
        return self._user_dir / USER_CONFIG_FILENAME

    @property
    def repo_config_path(self) -> Path | None:
        """Optional canonical path to `<repo_root>/.nyssa-ai/daily-tasks/config.json`."""
        return (self._repo_dir / USER_CONFIG_FILENAME) if self._repo_dir is not None else None

    @property
    def user_profile_path(self) -> Path:
        """Active read path (`<user_dir>/config.json`, or read-only fallback `<user_dir>/profile.json`)."""
        return _resolve_read_path(self._user_dir)

    @property
    def repo_profile_path(self) -> Path | None:
        """Optional active read path (`<repo_dir>/config.json`, or read-only fallback `<repo_dir>/profile.json`)."""
        return _resolve_read_path(self._repo_dir) if self._repo_dir is not None else None

    @property
    def templates_updates_path(self) -> Path:
        """Path to `<user_dir>/templates/updates.json`."""
        return self._user_dir / "templates" / "updates.json"

    def read_raw(self, path: Path) -> Result[dict[str, JsonValue] | None]:
        """Read a JSON object at `path` without requiring Schema Version 2 (returns `ok(None)` when absent)."""
        if path.is_symlink():
            return fail(f"Configuration file at {path.as_posix()} must not be a symlink.", ErrorCategory.VALIDATION)
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
                f"Configuration file at {path.as_posix()} must contain a JSON object.", ErrorCategory.VALIDATION
            )
        return ok(parsed)

    def read_strict_v2(self, path: Path) -> Result[dict[str, JsonValue] | None]:
        """Read `config.json` (or legacy `profile.json`) at `path`, requiring `schema_version == 2`."""
        loaded = self.read_raw(path)
        if not loaded.ok:
            return loaded
        doc = loaded.value
        if doc is None:
            return ok(None)
        if not _is_schema_v2(doc.get("schema_version")):
            return fail(
                f'Setup incomplete: {path.name} at {path.as_posix()} must declare "schema_version": 2 (run Setup).',
                ErrorCategory.VALIDATION,
            )
        telemetry_check = extract_telemetry_enabled(doc)
        if not telemetry_check.ok:
            return fail(telemetry_check.message, telemetry_check.category)
        return ok(doc)

    def read_layered(self, vault_root: Path | None = None) -> Result[dict[str, JsonValue]]:
        """Resolve configuration strictly across `user_home` -> `repo_root` (plus per-vault overrides)."""
        user_res = self.read_strict_v2(self.user_profile_path)
        if not user_res.ok:
            return fail(user_res.message, user_res.category)
        user_doc = user_res.value or {}
        merged = _merge_profile_layer({}, user_doc)

        vault_posix = vault_root.resolve().as_posix() if vault_root is not None else None
        if vault_posix is not None:
            merged = _apply_vault_section(merged, user_doc, vault_posix)

        if self.repo_profile_path is not None:
            repo_res = self.read_strict_v2(self.repo_profile_path)
            if not repo_res.ok:
                return fail(repo_res.message, repo_res.category)
            if repo_res.value is not None:
                merged = _merge_profile_layer(merged, repo_res.value)
                if vault_posix is not None:
                    merged = _apply_vault_section(merged, repo_res.value, vault_posix)

        return ok(merged)

    def write_user_config(self, payload: Mapping[str, JsonValue]) -> Result[None]:
        """Write canonical `<user_dir>/config.json` with private POSIX permissions (`0700` dir, `0600` file)."""
        path = self.user_config_path
        if path.is_symlink():
            return fail(f"Refusing to write through symlink at {path.as_posix()}.", ErrorCategory.VALIDATION)
        try:
            parent_existed = path.parent.exists()
            path.parent.mkdir(parents=True, exist_ok=True)
            if not parent_existed and os.name == "posix":
                path.parent.chmod(0o700)
            file_existed = path.exists()
            encoded = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
            path.write_text(encoded, encoding="utf-8", newline="\n")
            if not file_existed and os.name == "posix":
                path.chmod(0o600)
        except OSError as exc:
            return fail(f"Unable to write {path.as_posix()}: {exc}", ErrorCategory.VALIDATION)
        return ok(None)

    def write_user_profile(self, payload: Mapping[str, JsonValue]) -> Result[None]:
        """Persist user configuration strictly to canonical `<user_dir>/config.json`."""
        return self.write_user_config(payload)
