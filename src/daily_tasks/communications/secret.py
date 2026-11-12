"""Responsibility: Capture secrets and register a cloud key vault out-of-band from the command line.
Public interface:
+-- APPLICATION_NAME
+-- main
`-- secret(argv, keyring, vault_registry, input_provider, out, status_out)
"""

import argparse
import logging
import os
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Final, TextIO

from nyssa_ai_configuration import (
    BootstrapOptions,
    ConfigurationManifestReader,
    ConfigurationManifestWriter,
    Keyring,
    SecretCaptureMode,
    SecretInputProvider,
    VaultOptions,
)

from daily_tasks.communications.secret_capture_service import SecretCaptureService
from daily_tasks.communications.secret_receipt_fields import secret_receipt_fields
from daily_tasks.communications.vault_registry import VaultRegistry
from daily_tasks.logging_setup import logging_setup

APPLICATION_NAME: Final = "daily-tasks"
_COMMUNICATION: Final = "communication"
_VAULT_NAMESPACE: Final = "vault"


def secret(
    argv: Sequence[str] | None = None,
    keyring: Keyring | None = None,
    vault_registry: VaultRegistry | None = None,
    input_provider: SecretInputProvider | None = None,
    out: TextIO | None = None,
    status_out: TextIO | None = None,
) -> int:
    """Run one subcommand and return 0, or 1 when the store is unavailable or a capture fails."""
    registry = vault_registry if vault_registry is not None else VaultRegistry.default()
    args = _parser(registry).parse_args(argv)
    if not logging.getLogger("daily_tasks").handlers:
        logging_setup(os.environ)
    output = out if out is not None else sys.stdout
    config_dir = str(Path(args.config_dir).expanduser().resolve())
    manifest = str(Path(args.manifest).expanduser().resolve()) if args.manifest else None
    options = BootstrapOptions(
        application_name=APPLICATION_NAME, configuration_directory=config_dir, manifest_path=manifest
    )
    service = SecretCaptureService.create(options, registry, keyring, input_provider, status_out)
    if not service.ok:
        output.write(f"Configuration store unavailable: {service.message}\n")
        return 1
    mode = SecretCaptureMode(args.mode)
    for namespace, key, prompt, preferred, forced in _targets(args):
        captured = service.value.capture(namespace, key, prompt, preferred, forced, mode, args.timeout)
        if not captured.ok:
            output.write(f"Secret {namespace}/{key} was not stored: {captured.message}\n")
            return 1
        receipt = secret_receipt_fields(captured.value)
        where = f"{receipt['namespace']}/{receipt['key']} in {receipt['provider']}"
        output.write(f"Stored {where} at {receipt['stored_at']}.\n")
    if args.command == "vault":
        return _register_vault(args, config_dir, manifest, output)
    return 0


main: Final = secret
"""Console entry point; same as `secret`."""


type _Target = tuple[str, str, str | None, str | None, str | None]


def _targets(args: argparse.Namespace) -> list[_Target]:
    if args.command == "vault":
        prompt = f"Access token for the '{args.name}' {args.kind} vault"
        return [(_VAULT_NAMESPACE, f"{args.name}-access-token", prompt, "aesLocal", "aesLocal")]
    preferred, forced = args.provider, args.forced_provider
    if args.command == "capture":
        return [(args.namespace, args.key, args.prompt, preferred, forced)]
    if args.command == "slack":
        return [(_COMMUNICATION, "slack", "Slack token", preferred, forced)]
    targets: list[_Target] = [(_COMMUNICATION, "gmail-client-id", "Gmail OAuth client ID", preferred, forced)]
    if not args.no_client_secret:
        targets.append((_COMMUNICATION, "gmail-client-secret", "Gmail OAuth client secret", preferred, forced))
    return targets


def _register_vault(args: argparse.Namespace, config_dir: str, manifest: str | None, output: TextIO) -> int:
    """Point the application's manifest entry at the vault; its access token stays sealed locally."""
    settings = {"projectId": args.project_id, "organizationId": args.organization_id}
    vault = VaultOptions(
        name=args.name,
        kind=args.kind,
        endpoint=args.endpoint,
        credential=f"{_VAULT_NAMESPACE}/{args.name}-access-token",
        settings={key: value for key, value in settings.items() if value},
    )
    manifest_path = Path(manifest) if manifest else ConfigurationManifestReader.default_manifest_path()
    existing = ConfigurationManifestReader.read_application(manifest_path, APPLICATION_NAME)
    timeout = existing.value.lock_timeout_ms if existing.ok else None
    written = ConfigurationManifestWriter().provision_application(
        manifest_path, APPLICATION_NAME, config_dir, timeout, vault
    )
    if not written.ok:
        output.write(f"Vault '{args.name}' was not registered: {written.message}\n")
        return 1
    output.write(f"Vault '{args.name}' ({args.kind}) is registered; secrets can now target provider '{args.name}'.\n")
    return 0


def _parser(registry: VaultRegistry) -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="python -m daily_tasks.communications.secret", description=__doc__)
    parser.add_argument(
        "--config-dir",
        default=str(Path.home() / ".nyssa-ai" / "daily-tasks"),
        help="configuration directory (default: ~/.nyssa-ai/daily-tasks)",
    )
    parser.add_argument("--manifest", default=None, help="configuration manifest path (default: library default)")
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser("capture", help="store any secret at NAMESPACE/KEY")
    capture.add_argument("namespace")
    capture.add_argument("key")
    capture.add_argument("--prompt", default=None, help="message shown above the masked input")
    gmail = commands.add_parser("gmail", help="store the Gmail OAuth client id and secret")
    gmail.add_argument("--no-client-secret", action="store_true", help="the OAuth client has no secret")
    slack = commands.add_parser("slack", help="store the Slack token")
    vault = commands.add_parser("vault", help="store a vault access token and register the vault")
    vault.add_argument("--name", required=True, help="provider name secrets use to target this vault")
    vault.add_argument("--kind", required=True, choices=registry.kinds())
    vault.add_argument("--endpoint", default=None, help="vault server URL (default: provider default)")
    vault.add_argument("--project-id", default=None)
    vault.add_argument("--organization-id", default=None)
    for command in (capture, gmail, slack):
        command.add_argument("--provider", default=None, help="preferred storage provider (default: aesLocal)")
        command.add_argument("--forced-provider", default=None, help="store only in this provider")
    for command in (capture, gmail, slack, vault):
        command.add_argument("--mode", choices=[m.value for m in SecretCaptureMode], default="auto")
        command.add_argument("--timeout", type=float, default=120.0, help="seconds to wait for input")
    return parser


if __name__ == "__main__":
    sys.exit(main())
