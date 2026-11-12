"""Responsibility: Boot the bundled Daily Tasks MCP stdio server across python3 and uv host runtimes.
Public interface:
+-- PLUGIN_ROOT
+-- SRC_DIR
+-- launch
+-- launch_mcp(argv, which_uv, exec_uv)
`-- main()
"""

from __future__ import annotations

import os
import shutil
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import Final

PLUGIN_ROOT: Final = Path(__file__).resolve().parents[2]
SRC_DIR: Final = PLUGIN_ROOT / "src"


def _default_exec(executable: str, args: Sequence[str]) -> int:
    os.execv(executable, list(args))


def _extract_flag_value(args: Sequence[str], flag: str) -> str | None:
    prefix = f"{flag}="
    for index, token in enumerate(args):
        if token == flag and index + 1 < len(args):
            return args[index + 1]
        if token.startswith(prefix):
            return token[len(prefix) :]
    return None


def _bootstrap_runtime_root(forwarded: Sequence[str]) -> Path:
    cli_rt = _extract_flag_value(forwarded, "--runtime-root")
    if cli_rt and cli_rt.strip():
        return Path(cli_rt.strip()).expanduser().resolve()
    env_rt = os.environ.get("NYSSA_RUNTIME_ROOT", "").strip()
    if env_rt:
        return Path(env_rt).expanduser().resolve()
    cwd = Path.cwd().resolve()
    if (cwd / "SOUL.md").is_file() and (cwd / "IDENTITY.md").is_file():
        return cwd
    return (Path.home() / ".nyssa-ai" / "daily-tasks" / "runtime").resolve()


def launch_mcp(
    argv: Sequence[str] | None = None,
    which_uv: Callable[[str], str | None] = shutil.which,
    exec_uv: Callable[[str, Sequence[str]], int] = _default_exec,
) -> int:
    """Run `daily_tasks.cli:cli` directly when dependencies import cleanly, else delegate to `uv run`."""
    forwarded = list(argv) if argv is not None else sys.argv[1:]
    src_path = str(SRC_DIR)
    if src_path not in sys.path:
        sys.path.insert(0, src_path)

    try:
        from daily_tasks.cli import cli
    except ModuleNotFoundError as exc:
        uv_bin = which_uv("uv")
        if uv_bin is not None:
            if not os.environ.get("UV_PROJECT_ENVIRONMENT", "").strip():
                runtime_root = _bootstrap_runtime_root(forwarded)
                os.environ["UV_PROJECT_ENVIRONMENT"] = str(runtime_root / ".venv")
            uv_args = [uv_bin, "run", "--no-dev"]
            if (PLUGIN_ROOT / "uv.lock").is_file():
                uv_args.append("--frozen")
            uv_args.extend(["--directory", str(PLUGIN_ROOT), "daily-tasks-mcp", *forwarded])
            return exec_uv(uv_bin, uv_args)
        sys.stderr.write(
            f"daily-tasks-mcp could not start: missing Python dependency ({exc.name}) in {sys.executable} "
            f"and 'uv' was not found on PATH. Install uv on PATH or pre-sync runtime dependencies for {PLUGIN_ROOT}.\n"
        )
        return 2

    return cli(forwarded)


launch: Final = launch_mcp


def main() -> int:
    """Console/script entry point for `.mcp.json` and portable `mcp.json` bundles."""
    return launch_mcp()


if __name__ == "__main__":
    raise SystemExit(main())
