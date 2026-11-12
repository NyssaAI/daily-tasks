"""Responsibility: Boot the bundled Daily Tasks MCP stdio server across python3 and uv host runtimes.
Public interface:
+-- PLUGIN_ROOT
+-- SRC_DIR
+-- launch(argv, which_uv, exec_uv)
`-- main()

Portable stdio launcher invoked from `.mcp.json`, `mcp.json`, and `mcp_config.json` without requiring `PYTHONPATH`
environment overrides or a globally installed `uv` binary when runtime dependencies are already available in Python.
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


def launch(
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
            return exec_uv(uv_bin, [uv_bin, "run", "--directory", str(PLUGIN_ROOT), "daily-tasks-mcp", *forwarded])
        sys.stderr.write(
            f"daily-tasks-mcp could not start: missing Python dependency ({exc.name}) in {sys.executable} "
            f"and 'uv' was not found on PATH. Install uv or run '{sys.executable} -m pip install -e {PLUGIN_ROOT}'.\n"
        )
        return 2

    return cli(forwarded)


def main() -> int:
    """Console/script entry point for `.mcp.json` and portable `mcp.json` bundles."""
    return launch()


if __name__ == "__main__":
    raise SystemExit(main())
