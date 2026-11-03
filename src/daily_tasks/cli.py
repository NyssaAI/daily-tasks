# Responsibility: Compose and run the Daily Tasks MCP stdio server from command-line settings.
# Public interface:
# +-- cli(argv, environ, stdin, stdout)
# `-- main
"""`daily-tasks-mcp --workspace-root DIR --user-email ADDR --timezone ZONE`: serve MCP over stdio.

Roots resolve against the absolute workspace root, never the working directory. Unset options reuse
`<workspace>/.nyssa-ai/daily-tasks/profile.json` (`user`, `timezone`, `projectsRoot`, `dailyPlansRelative`).
"""

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Mapping, Sequence
from datetime import UTC, datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Final, TextIO

from pydantic import JsonValue

from daily_tasks.domain import GraphUser
from daily_tasks.logging_setup import logging_setup
from daily_tasks.server.markdown_workspace_reader import MarkdownWorkspaceReader
from daily_tasks.server.mcp_server import McpServer
from daily_tasks.server.new_uuid7 import new_uuid7
from daily_tasks.server.planning_tools import PlanningTools
from daily_tasks.server.serve_stdio import serve_stdio
from daily_tasks.server.types import ServerSettings
from daily_tasks.storage.markdown_file_store import MarkdownFileStore

_STATE: Final = Path(".nyssa-ai") / "daily-tasks"


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _profile(workspace: Path) -> Mapping[str, JsonValue]:
    path = workspace / _STATE / "profile.json"
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}
    return loaded if isinstance(loaded, dict) else {}


def _text(profile: Mapping[str, JsonValue], *keys: str) -> str | None:
    value: JsonValue = dict(profile)
    for key in keys:
        value = value.get(key) if isinstance(value, dict) else None
    return value if isinstance(value, str) and value.strip() else None


def _root(workspace: Path, value: str | None, default: str) -> Path:
    path = Path(value or default).expanduser()
    return path if path.is_absolute() else (workspace / path).resolve()


def _settings(args: argparse.Namespace) -> ServerSettings | str:
    workspace = Path(args.workspace_root).expanduser()
    if not workspace.is_absolute():
        return "--workspace-root must be an absolute path."
    profile = _profile(workspace)
    email = args.user_email or _text(profile, "user", "email")
    timezone = args.timezone or _text(profile, "timezone")
    if not email or not timezone or timezone == "system":
        return "Set --user-email and --timezone (IANA), or store user.email and timezone in profile.json."
    name = args.user_name or _text(profile, "user", "name") or email
    return ServerSettings(
        workspace_root=workspace,
        projects_root=_root(workspace, args.projects_root or _text(profile, "projectsRoot"), "projects"),
        daily_plans_root=_root(workspace, args.daily_plans_root or _text(profile, "dailyPlansRelative"), "daily-plans"),
        state_root=workspace / _STATE,
        user=GraphUser(name=name, email=email),
        timezone=timezone,
    )


def _version() -> str:
    try:
        return version("daily-tasks")
    except PackageNotFoundError:
        return "0.0.0"


def cli(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    stdin: TextIO | None = None,
    stdout: TextIO | None = None,
) -> int:
    """Serve until stdin closes and return 0, or return 2 for missing settings (reported on stderr)."""
    env = environ if environ is not None else os.environ
    args = _parser(env).parse_args(argv)
    logger = logging_setup("daily_tasks.server", env, args.log_file)
    settings = _settings(args)
    if isinstance(settings, str):
        logger.error("server not started", fields={"reason": settings}, operation="mcp.start")
        sys.stderr.write(settings + "\n")
        return 2
    store = MarkdownFileStore(
        settings.workspace_root,
        logger,
        _utc_now,
        records_root=settings.projects_root,
        daily_plans_root=settings.daily_plans_root,
        state_root=settings.state_root,
    )
    reader = MarkdownWorkspaceReader(settings, logger)
    tools = PlanningTools(settings, reader, store, logger, _utc_now, new_uuid7)
    server = McpServer(tools, logger, _version())
    logger.info("server started", fields={"version": _version()}, operation="mcp.start")
    return asyncio.run(serve_stdio(server, stdin or sys.stdin, stdout or sys.stdout))


main: Final = cli
"""Console entry point (`daily-tasks-mcp`); same as `cli`."""


def _parser(environ: Mapping[str, str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="daily-tasks-mcp", description=__doc__)
    parser.add_argument("--workspace-root", default=environ.get("DAILY_TASKS_WORKSPACE_ROOT") or os.getcwd())
    parser.add_argument("--projects-root", default=None, help="absolute or workspace-relative (default: projects)")
    parser.add_argument(
        "--daily-plans-root", default=None, help="absolute or workspace-relative (default: daily-plans)"
    )
    parser.add_argument("--user-email", default=environ.get("DAILY_TASKS_USER_EMAIL"))
    parser.add_argument("--user-name", default=environ.get("DAILY_TASKS_USER_NAME"))
    parser.add_argument("--timezone", default=environ.get("DAILY_TASKS_TIMEZONE"), help="IANA timezone")
    parser.add_argument("--log-file", default=None, help="also write JSON log records to this file")
    return parser


if __name__ == "__main__":
    sys.exit(main())
