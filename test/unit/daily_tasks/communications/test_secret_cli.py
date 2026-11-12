"""Responsibility: Prove the secret command stores secrets out-of-band and prints only sanitized receipts.
Public interface:
+-- SECRET
+-- test_secret_cli_capture_stores_secret_and_prints_receipt_only(tmp_path)
+-- test_secret_cli_gmail_stores_client_id_and_secret(tmp_path)
+-- test_secret_cli_unavailable_forced_provider_returns_one(tmp_path)
`-- test_secret_cli_vault_seals_token_locally_and_registers_vault(tmp_path)

`python -m daily_tasks.communications.secret` behavior with a scripted input provider and an in-memory keyring.
"""

import io
import json
from dataclasses import dataclass, field
from pathlib import Path

from nyssa_ai_configuration import CapturedSecret, KeyringInMemory, SecretPromptRequest
from nyssa_ai_result import Ok, Result, ok

from daily_tasks.communications import SecretResolver, VaultRegistry
from daily_tasks.communications.secret import APPLICATION_NAME, main

SECRET = "xoxb-cli-secret-token"


@dataclass
class _ScriptedInput:
    value: str = SECRET
    requests: list[SecretPromptRequest] = field(default_factory=list)

    def capture(self, request: SecretPromptRequest) -> Result[CapturedSecret]:
        self.requests.append(request)
        return ok(CapturedSecret(self.value, request.preferred_provider))


def _argv(root: Path, *command: str) -> list[str]:
    return ["--config-dir", str(root / "config"), "--manifest", str(root / "manifest.json"), *command, "--mode", "cli"]


def _resolve(root: Path, keyring: KeyringInMemory, namespace: str, key: str) -> str:
    resolver = SecretResolver.create(
        APPLICATION_NAME, str(root / "config"), keyring, {}, str(root / "manifest.json")
    )
    assert isinstance(resolver, Ok)
    resolved = resolver.value.resolve(namespace, key)
    assert isinstance(resolved, Ok)
    return resolved.value.reveal()


def test_secret_cli_capture_stores_secret_and_prints_receipt_only(tmp_path: Path) -> None:
    keyring, out, status = KeyringInMemory(), io.StringIO(), io.StringIO()

    code = main(_argv(tmp_path, "capture", "plugins", "api-key"), keyring, None, _ScriptedInput(), out, status)

    assert code == 0
    assert "Stored plugins/api-key in aesLocal at " in out.getvalue()
    assert SECRET not in out.getvalue() + status.getvalue()
    assert _resolve(tmp_path, keyring, "plugins", "api-key") == SECRET


def test_secret_cli_gmail_stores_client_id_and_secret(tmp_path: Path) -> None:
    keyring, user = KeyringInMemory(), _ScriptedInput()

    code = main(_argv(tmp_path, "gmail"), keyring, None, user, io.StringIO(), io.StringIO())

    assert code == 0
    assert [(r.namespace, r.key) for r in user.requests] == [
        ("communication", "gmail-client-id"),
        ("communication", "gmail-client-secret"),
    ]
    assert _resolve(tmp_path, keyring, "communication", "gmail-client-secret") == SECRET


def test_secret_cli_unavailable_forced_provider_returns_one(tmp_path: Path) -> None:
    out = io.StringIO()
    argv = _argv(tmp_path, "slack", "--forced-provider", "missing")

    code = main(argv, KeyringInMemory(), None, _ScriptedInput(), out, io.StringIO())

    assert code == 1
    assert "communication/slack was not stored" in out.getvalue()
    assert SECRET not in out.getvalue()


def test_secret_cli_vault_seals_token_locally_and_registers_vault(tmp_path: Path) -> None:
    keyring, out = KeyringInMemory(), io.StringIO()
    argv = _argv(tmp_path, "vault", "--name", "bws", "--kind", "bitwarden-secrets", "--project-id", "p-1")

    code = main(argv, keyring, VaultRegistry.default(), _ScriptedInput(), out, io.StringIO())

    assert code == 0, out.getvalue()
    assert "Stored vault/bws-access-token in aesLocal" in out.getvalue()
    manifest = json.loads((tmp_path / "manifest.json").read_text(encoding="utf-8"))
    key_vault = manifest["applications"][APPLICATION_NAME]["keyVault"]
    assert key_vault == {
        "name": "bws",
        "kind": "bitwarden-secrets",
        "credential": "vault/bws-access-token",
        "settings": {"projectId": "p-1"},
    }
    disk = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tmp_path.rglob("*") if p.is_file())
    assert SECRET not in disk
    assert _resolve(tmp_path, keyring, "vault", "bws-access-token") == SECRET
