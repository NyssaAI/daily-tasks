"""Responsibility: Deterministically resolve runtime_root across CLI, env, agent persona cwd, and profile defaults.
Public interface:
+-- RUNTIME_ROOT_ENV_VAR
+-- is_agent_runtime_root(path)
`-- resolve_runtime_root(explicit, environ, cwd, configured, config_dir)
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
) -> Result[Path]:
    """Resolve `runtime_root` via the 4-step deterministic precedence chain.

    Precedence:
    1. Explicit `--runtime-root` / `ServerOverrides.runtime_root`
    2. `NYSSA_RUNTIME_ROOT` environment variable
    3. `cwd` when containing `SOUL.md` + `IDENTITY.md` (`is_agent_runtime_root`)
    4. Configured `runtimeRoot` in `.nyssa-ai/daily-tasks/`, else `<user_config_dir>/runtime/`
    """
    if explicit is not None:
        return _validate_absolute(explicit, "--runtime-root")

    env = environ if environ is not None else os.environ
    env_raw = env.get(RUNTIME_ROOT_ENV_VAR, "").strip()
    if env_raw:
        return _validate_absolute(Path(env_raw), RUNTIME_ROOT_ENV_VAR)

    effective_cwd = (cwd if cwd is not None else Path.cwd()).resolve()
    if is_agent_runtime_root(effective_cwd):
        return ok(effective_cwd)

    if configured and configured.strip():
        return _validate_absolute(Path(configured.strip()), "runtimeRoot")

    base_config = (
        config_dir.expanduser().resolve() if config_dir is not None else (Path.home() / _DEFAULT_APP_SUBDIR).resolve()
    )
    return ok((base_config / "runtime").resolve())
