"""Responsibility: Deterministically resolve runtime_root across CLI, env, agent persona cwd, and config defaults.
Public interface:
+-- RUNTIME_ROOT_ENV_VAR
+-- is_agent_runtime_root(path)
`-- resolve_runtime_root(explicit, environ, cwd, configured, config_dir, repo_root)
"""

from __future__ import annotations

import os
from collections.abc import Mapping
from pathlib import Path
from typing import Final

from nyssa_ai_result import ErrorCategory, Result, fail, ok

RUNTIME_ROOT_ENV_VAR: Final = "NYSSA_RUNTIME_ROOT"
_DEFAULT_APP_SUBDIR: Final = Path(".nyssa-ai") / "daily-tasks"


def is_agent_runtime_root(path: Path) -> bool:
    """Return True when `path` is an agent persona runtime root containing `SOUL.md` and `IDENTITY.md`."""
    return (path / "SOUL.md").is_file() and (path / "IDENTITY.md").is_file()


def _validate_absolute(candidate: Path, label: str) -> Result[Path]:
    expanded = candidate.expanduser()
    if not expanded.is_absolute():
        return fail(f"{label} must be an absolute path.", ErrorCategory.VALIDATION)
    return ok(expanded.resolve())


def resolve_runtime_root(
    explicit: Path | None = None,
    environ: Mapping[str, str] | None = None,
    cwd: Path | None = None,
    configured: str | None = None,
    config_dir: Path | None = None,
    repo_root: Path | None = None,
) -> Result[Path]:
    """Resolve `runtime_root` via the 4-step deterministic precedence chain.

    Precedence:
    1. Explicit `--runtime-root` / `ServerOverrides.runtime_root`
    2. `NYSSA_RUNTIME_ROOT` environment variable (routing `SOUL.md` + `IDENTITY.md` roots to
       `.nyssa-ai/daily-tasks/runtime`)
    3. `cwd` when containing `SOUL.md` + `IDENTITY.md` -> `<cwd>/.nyssa-ai/daily-tasks/runtime`
    4. Configured `runtimeRoot` in layered `config.json`, else `<repo_root>/.nyssa-ai/daily-tasks/runtime` when
       `<repo_root>/.nyssa-ai/daily-tasks` exists, else `<user_config_dir>/runtime/`
    """
    if explicit is not None:
        return _validate_absolute(explicit, "--runtime-root")

    env = environ if environ is not None else os.environ
    env_raw = env.get(RUNTIME_ROOT_ENV_VAR, "").strip()
    if env_raw:
        env_res = _validate_absolute(Path(env_raw), RUNTIME_ROOT_ENV_VAR)
        if not env_res.ok:
            return env_res
        env_dir = env_res.value
        if is_agent_runtime_root(env_dir):
            return ok((env_dir / _DEFAULT_APP_SUBDIR / "runtime").resolve())
        return ok(env_dir)

    effective_cwd = (cwd if cwd is not None else Path.cwd()).expanduser().resolve()
    if is_agent_runtime_root(effective_cwd):
        return ok((effective_cwd / _DEFAULT_APP_SUBDIR / "runtime").resolve())

    if configured and configured.strip():
        return _validate_absolute(Path(configured.strip()), "runtimeRoot")

    if repo_root is not None:
        repo_res = _validate_absolute(repo_root, "--repo-root")
        if not repo_res.ok:
            return repo_res
        repo_app_dir = repo_res.value / _DEFAULT_APP_SUBDIR
        if repo_app_dir.is_dir():
            return ok((repo_app_dir / "runtime").resolve())

    base_config = (
        config_dir.expanduser().resolve() if config_dir is not None else (Path.home() / _DEFAULT_APP_SUBDIR).resolve()
    )
    return ok((base_config / "runtime").resolve())
