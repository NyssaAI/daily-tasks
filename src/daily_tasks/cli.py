"""Responsibility: Compose and run the Daily Tasks MCP stdio server from command-line settings.
Public interface:
+-- cli(argv, environ, stdin, stdout)
`-- main
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

from daily_tasks.hosting.compose_mcp_server import compose_mcp_server
from daily_tasks.hosting.new_uuid7 import new_uuid7
from daily_tasks.hosting.resolve_runtime_root import RUNTIME_ROOT_ENV_VAR, is_agent_runtime_root
from daily_tasks.hosting.types import ServerOverrides
from daily_tasks.logging_setup import logging_setup
from daily_tasks.transports.mcp.serve_stdio import serve_stdio

_LOGGER: Final = logging.getLogger(__name__)


def _utc_now() -> datetime:
    return datetime.now(UTC)


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


def _require_absolute(raw: str | None, flag: str) -> tuple[bool, Path | None, str | None]:
    if not raw:
        return True, None, None
    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        return False, None, f"{flag} must be an absolute path."
    return True, candidate, None


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

    ok_vault, default_vault, err_vault = _require_absolute(args.vault_root, "--vault-root")
    if not ok_vault and err_vault is not None:
        _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": err_vault}})
        sys.stderr.write(err_vault + "\n")
        return 2
    if default_vault is not None and is_agent_runtime_root(default_vault.resolve()):
        reason = (
            f"Refusing to use agent runtime root {default_vault.resolve().as_posix()} "
            "(contains SOUL.md and IDENTITY.md) as --vault-root."
        )
        _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": reason}})
        sys.stderr.write(reason + "\n")
        return 2

    ok_rt, runtime_root, err_rt = _require_absolute(args.runtime_root, "--runtime-root")
    if not ok_rt and err_rt is not None:
        _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": err_rt}})
        sys.stderr.write(err_rt + "\n")
        return 2

    ok_repo, repo_root, err_repo = _require_absolute(args.repo_root, "--repo-root")
    if not ok_repo and err_repo is not None:
        _LOGGER.error("server not started", extra={"operation": "mcp.start", "fields": {"reason": err_repo}})
        sys.stderr.write(err_repo + "\n")
        return 2

    resolved_config_dir = Path(args.config_dir).expanduser().resolve()
    overrides = ServerOverrides(
        vault_root=default_vault,
        projects_root=args.projects_root,
        daily_plans_root=args.daily_plans_root,
        runtime_root=runtime_root,
        repo_root=repo_root,
        user_email=args.user_email,
        user_name=args.user_name,
        timezone=args.timezone,
        initial_lookback_days=args.initial_lookback_days,
        config_dir=resolved_config_dir,
    )
    resolved_version = _version()
    server = compose_mcp_server(
        overrides=overrides,
        version=resolved_version,
        clock=_utc_now,
        new_id=new_uuid7,
        environ=env,
    )
    _LOGGER.info("server started", extra={"operation": "mcp.start", "fields": {"version": resolved_version}})
    return asyncio.run(serve_stdio(server, stdin or sys.stdin, stdout or sys.stdout))


main: Final = cli
"""Console entry point (`daily-tasks-mcp`); same as `cli`."""


def _parser(environ: Mapping[str, str]) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="daily-tasks-mcp", description=__doc__)
    parser.add_argument("--vault-root", default=environ.get("DAILY_TASKS_VAULT_ROOT"))
    parser.add_argument("--runtime-root", default=environ.get(RUNTIME_ROOT_ENV_VAR))
    parser.add_argument("--repo-root", default=environ.get("DAILY_TASKS_REPO_ROOT"))
    parser.add_argument("--projects-root", default=None, help="absolute or vault-relative (default: 1-projects)")
    parser.add_argument(
        "--daily-plans-root", default=None, help="absolute or vault-relative (default: 2-areas/daily-plans)"
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
