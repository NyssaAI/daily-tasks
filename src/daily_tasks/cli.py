"""Responsibility: Compose and run the Daily Tasks MCP stdio server from command-line settings.
Public interface:
+-- cli(argv, environ, stdin, stdout)
`-- main

`daily-tasks-mcp [--workspace-root DIR]`: serve MCP over stdio.

Roots resolve against the absolute workspace root, never the working directory. Unset options reuse
user (`~/.nyssa-ai/daily-tasks/profile.json`) and workspace (`<workspace>/.nyssa-ai/daily-tasks/profile.json`)
profiles (`user`, `timezone`, `projectsRoot`, `dailyPlansRelative`, `sources.initialLookbackDays` or
`initialLookbackDays`). Fetch cursors live in `<state_root>/fetch-cursors.json`.
"""

import argparse
import asyncio
import json
import logging
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Final, TextIO

from nyssa_ai_configuration import BootstrapOptions
from nyssa_ai_result import Result

from daily_tasks.credentials import SecretCaptureService
from daily_tasks.logging_setup import logging_setup
from daily_tasks.server.mcp_server import McpServer
from daily_tasks.server.new_uuid7 import new_uuid7
from daily_tasks.server.planning_tools_dispatcher import PlanningToolsDispatcher
from daily_tasks.server.secret_tools import SecretTools
from daily_tasks.server.serve_stdio import serve_stdio
from daily_tasks.server.setup_tools import SetupTools
from daily_tasks.server.types import ServerOverrides

_LOGGER: Final = logging.getLogger(__name__)
_APPLICATION_NAME: Final = "daily-tasks"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _secret_tools(config_dir: Path) -> SecretTools:
    options = BootstrapOptions(application_name=_APPLICATION_NAME, configuration_directory=str(config_dir))

    def open_service() -> Result[SecretCaptureService]:
        return SecretCaptureService.create(options)

    return SecretTools(open_service)


def _version() -> str:
    try:
        return version("daily-tasks")
    except PackageNotFoundError:
        manifest = Path(__file__).resolve().parents[2] / "plugin.json"
        try:
            data = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return "0.0.0"
        ver = data.get("version") if isinstance(data, dict) else None
        return ver if isinstance(ver, str) and ver else "0.0.0"


def cli(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Serve until stdin closes and return 0, or return 2 for invalid CLI arguments (reported on stderr)."""
    env = environ if environ is not None else os.environ
    args = _parser(env).parse_args(argv)
    logging_setup(env, args.log_file)
    if args.initial_lookback_days is not None and args.initial_lookback_days <= 0:
        message = "Initial lookback days must be a positive integer (--initial-lookback-days or initialLookbackDays)."
        _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": message}})
        sys.stderr.write(message + "\n")
        return 2

    default_workspace = None
    if args.workspace_root:
        candidate = Path(args.workspace_root).expanduser()
        if not candidate.is_absolute():
            message = "--workspace-root must be an absolute path."
            _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": message}})
            sys.stderr.write(message + "\n")
            return 2
        default_workspace = candidate

    resolved_config_dir = Path(args.config_dir).expanduser().resolve()
    overrides = ServerOverrides(
        workspace_root=default_workspace,
        user_email=args.user_email,
        user_name=args.user_name,
        timezone=args.timezone,
        projects_root=args.projects_root,
        daily_plans_root=args.daily_plans_root,
        initial_lookback_days=args.initial_lookback_days,
        config_dir=resolved_config_dir,
    )
    resolved_version = _version()
    dispatcher = PlanningToolsDispatcher(
        overrides=overrides,
        clock=_utc_now,
        new_id=new_uuid7,
    )
    setup_tools = SetupTools(overrides=overrides, clock=_utc_now, plugin_version=resolved_version)
    server = McpServer(dispatcher, resolved_version, _secret_tools(resolved_config_dir), setup_tools)
    _LOGGER.info("server started", extra={"operation": "mcp.start", "fields": {"version": resolved_version}})
    return asyncio.run(serve_stdio(server, stdin or sys.stdin, stdout or sys.stdout))


main: Final = cli
"""Console entry point (`daily-tasks-mcp`); same as `cli`."""


def _parser(environ: Mapping[str, str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="daily-tasks-mcp", description=__doc__)
    parser.add_argument("--workspace-root", default=environ.get("DAILY_TASKS_WORKSPACE_ROOT"))
    parser.add_argument("--projects-root", default=None, help="absolute or workspace-relative (default: projects)")
    parser.add_argument(
        "--daily-plans-root", default=None, help="absolute or workspace-relative (default: daily-plans)"
    )
    parser.add_argument("--user-email", default=environ.get("DAILY_TASKS_USER_EMAIL"))
    parser.add_argument("--user-name", default=environ.get("DAILY_TASKS_USER_NAME"))
    parser.add_argument("--timezone", default=environ.get("DAILY_TASKS_TIMEZONE"), help="IANA timezone")
    parser.add_argument(
        "--initial-lookback-days",
        type=int,
        default=None,
        help="days a source's first pull reaches back when it has no saved cursor (default: 7)",
    )
    parser.add_argument("--log-file", default=None, help="also write JSON log records to this file")
    parser.add_argument(
        "--config-dir",
        default=str(Path.home() / ".nyssa-ai" / "daily-tasks"),
        help="user profile and secret configuration directory (default: ~/.nyssa-ai/daily-tasks)",
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
