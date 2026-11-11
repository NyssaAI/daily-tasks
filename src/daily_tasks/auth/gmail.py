"""Responsibility: Run the interactive Gmail read-only sign-in from the command line.
Public interface:
+-- APPLICATION_NAME
+-- CLIENT_ID_ENV_VAR
+-- CLIENT_SECRET_ENV_VAR
+-- gmail(argv, environ, keyring, http_post, browser_launcher, out)
`-- main

`python -m daily_tasks.auth.gmail [--config-dir DIR]`: seal a `gmail.readonly` grant in the keyring store.
"""

import argparse
import logging
import os
import sys
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path
from typing import Final, TextIO

from nyssa_ai_configuration import BootstrapOptions, BrowserLauncher, Keyring
from nyssa_ai_result import Result

from daily_tasks.adapters.communication.gmail_oauth import GmailOauth
from daily_tasks.credentials import SecretResolver
from daily_tasks.logging_setup import logging_setup

APPLICATION_NAME: Final = "daily-tasks"
CLIENT_ID_ENV_VAR: Final = "GMAIL_CLIENT_ID"
CLIENT_SECRET_ENV_VAR: Final = "GMAIL_CLIENT_SECRET"


def gmail(
    argv: Sequence[str] | None = None,
    environ: Mapping[str, str] | None = None,
    keyring: Keyring | None = None,
    http_post: Callable[[str, Mapping[str, str]], Result[tuple[int, str]]] | None = None,
    browser_launcher: BrowserLauncher | None = None,
    out: TextIO | None = None,
) -> int:
    """Sign in and return 0, or 1 when credentials are missing or sign-in fails (never prints tokens).

    The OAuth client id/secret come from `GMAIL_CLIENT_ID`/`GMAIL_CLIENT_SECRET` or the sealed
    `communication/gmail-client-id` and `communication/gmail-client-secret` entries.
    """
    args = _parser().parse_args(argv)
    env = environ if environ is not None else os.environ
    if not logging.getLogger("daily_tasks").handlers:
        logging_setup(env)
    output = out if out is not None else sys.stdout
    config_dir = str(Path(args.config_dir).expanduser().resolve())
    manifest = str(Path(args.manifest).expanduser().resolve()) if args.manifest else None
    resolver = SecretResolver.create(APPLICATION_NAME, config_dir, keyring, env, manifest)
    if not resolver.ok:
        output.write(f"Configuration store unavailable: {resolver.message}\n")
        return 1
    client_id = resolver.value.resolve(GmailOauth.DEFAULT_NAMESPACE, "gmail-client-id", CLIENT_ID_ENV_VAR)
    if not client_id.ok:
        output.write(f"Set {CLIENT_ID_ENV_VAR} or store communication/gmail-client-id first.\n")
        return 1
    client_secret = resolver.value.resolve(GmailOauth.DEFAULT_NAMESPACE, "gmail-client-secret", CLIENT_SECRET_ENV_VAR)
    options = BootstrapOptions(
        application_name=APPLICATION_NAME, configuration_directory=config_dir, manifest_path=manifest
    )
    oauth = GmailOauth.create(
        options,
        client_id.value,
        client_secret.value if client_secret.ok else None,
        keyring=keyring,
        http_post=http_post,
        browser_launcher=browser_launcher,
    )
    if not oauth.ok:
        output.write(f"Configuration store unavailable: {oauth.message}\n")
        return 1
    authorized = oauth.value.authorize(redirect_port=args.redirect_port)
    if not authorized.ok:
        output.write(f"Gmail sign-in failed: {authorized.message}\n")
        return 1
    output.write("Gmail read-only access authorized; the grant is stored sealed.\n")
    return 0


main: Final = gmail
"""Console entry point; same as `gmail`."""


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m daily_tasks.auth.gmail", description=__doc__)
    parser.add_argument(
        "--config-dir",
        default=str(Path.home() / ".nyssa-ai" / "daily-tasks"),
        help="configuration directory (default: ~/.nyssa-ai/daily-tasks)",
    )
    parser.add_argument("--manifest", default=None, help="configuration manifest path (default: library default)")
    parser.add_argument(
        "--redirect-port",
        type=int,
        default=None,
        help="fixed 127.0.0.1 loopback port for SSH port-forwarded headless OAuth callbacks (default: ephemeral)",
    )
    return parser


if __name__ == "__main__":
    sys.exit(main())
