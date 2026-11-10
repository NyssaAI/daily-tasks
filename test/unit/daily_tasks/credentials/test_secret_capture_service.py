"""Responsibility: Prove SecretCaptureService stores captured secrets and exposes only sanitized receipts.
Public interface:
+-- APP
+-- SECRET
+-- test_capture_secret_loopback_page_stores_posted_secret(tmp_path)
+-- test_capture_secret_registered_vault_factory_offers_and_stores_in_vault(tmp_path)
+-- test_capture_secret_stores_sealed_and_returns_sanitized_receipt(tmp_path, log_capture)
+-- test_capture_secret_unavailable_forced_provider_fails_validation(tmp_path, log_capture)
+-- test_create_unregistered_vault_kind_fails_validation(tmp_path, log_capture)
+-- test_secret_resolver_reads_secret_through_registered_vault(tmp_path)
`-- test_vault_registry_default_registers_bitwarden_kinds()

Out-of-band capture with a scripted input provider, an in-memory keyring and fake vault factories.
"""

import io
import threading
import urllib.parse
import urllib.request
from dataclasses import dataclass, field
from pathlib import Path

from nyssa_ai_configuration import (
    BootstrapOptions,
    CapturedSecret,
    CloudKeyVault,
    CloudKeyVaultRecovery,
    ConfigurationPointer,
    KeyringInMemory,
    LoopbackSecretInputProvider,
    OAuthOptions,
    SecretCaptureMode,
    SecretPromptRequest,
    VaultOptions,
)
from nyssa_ai_configuration.cloud_key_vaults.access_token_source import AccessTokenSource
from nyssa_ai_result import Err, Ok, Result, fail, ok

from conftest import LogCapture
from daily_tasks.credentials import SecretCaptureService, SecretResolver, VaultRegistry

APP = "daily-tasks-test"
SECRET = "gocspx-very-secret-value"


@dataclass
class _ScriptedInput:
    """Stands in for the user: answers every prompt with `value`, choosing `provider` or the preselection."""

    value: str
    provider: str | None = None
    requests: list[SecretPromptRequest] = field(default_factory=list)

    def capture(self, request: SecretPromptRequest) -> Result[CapturedSecret]:
        self.requests.append(request)
        return ok(CapturedSecret(self.value, self.provider or request.preferred_provider))


@dataclass
class _MemoryVault:
    name: str
    values: dict[str, str] = field(default_factory=dict)

    @property
    def recovery(self) -> CloudKeyVaultRecovery | None:
        return None

    def read(self, pointer: ConfigurationPointer) -> Result[str]:
        found = self.values.get(pointer.value)
        return ok(found) if found is not None else fail("missing", "NotFound")

    def write(self, namespace: str, key: str, value: str) -> Result[ConfigurationPointer]:
        self.values[f"{namespace}.{key}"] = value
        return ok(ConfigurationPointer(self.name, f"{namespace}.{key}"))

    def remove(self, pointer: ConfigurationPointer) -> Result[bool]:
        return ok(self.values.pop(pointer.value, None) is not None)


@dataclass
class _MemoryVaultFactory:
    vault: _MemoryVault
    kind: str = "memory-vault"

    def create(self, options: VaultOptions, token_source: AccessTokenSource | None = None) -> Result[CloudKeyVault]:
        return ok(self.vault)

    def authorization(self, options: VaultOptions) -> Result[OAuthOptions | None]:
        return ok(None)


def _options(root: Path, vault: VaultOptions | None = None) -> BootstrapOptions:
    return BootstrapOptions(
        application_name=APP,
        configuration_directory=str(root / "config"),
        manifest_path=str(root / "manifest.json"),
        key_vault=vault,
    )


def _service(
    root: Path,
    keyring: KeyringInMemory,
    user: _ScriptedInput,
    vaults: VaultRegistry | None = None,
    vault: VaultOptions | None = None,
) -> SecretCaptureService:
    created = SecretCaptureService.create(_options(root, vault), vaults, keyring, user, io.StringIO())
    assert isinstance(created, Ok)
    return created.value


def _disk(root: Path) -> str:
    return "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in root.rglob("*") if p.is_file())


def test_capture_secret_stores_sealed_and_returns_sanitized_receipt(tmp_path: Path, log_capture: LogCapture) -> None:
    keyring, user = KeyringInMemory(), _ScriptedInput(SECRET)

    captured = _service(tmp_path, keyring, user).capture("communication", "gmail-client-secret", "Gmail secret")

    assert isinstance(captured, Ok)
    receipt = captured.value
    assert (receipt.namespace, receipt.key, receipt.provider) == ("communication", "gmail-client-secret", "aesLocal")
    assert SECRET not in repr(receipt) + repr(log_capture.records) + _disk(tmp_path)
    assert log_capture.records[-1][1] == "secret captured"
    assert set(log_capture.records[-1][2]) == {"namespace", "key", "provider", "stored_at", "elapsed_ms"}
    assert user.requests[0].prompt_message == "Gmail secret"
    assert user.requests[0].available_providers == ["aesLocal", "literal"]
    resolver = SecretResolver.create(APP, str(tmp_path / "config"), keyring, {}, str(tmp_path / "manifest.json"))
    assert isinstance(resolver, Ok)
    resolved = resolver.value.resolve("communication", "gmail-client-secret")
    assert isinstance(resolved, Ok) and resolved.value.reveal() == SECRET


def test_capture_secret_unavailable_forced_provider_fails_validation(tmp_path: Path, log_capture: LogCapture) -> None:
    captured = _service(tmp_path, KeyringInMemory(), _ScriptedInput(SECRET)).capture(
        "communication", "slack", forced_provider="no-such-vault"
    )

    assert isinstance(captured, Err)
    assert captured.category == "Validation"
    assert log_capture.records[-1][0:2] == ("warn", "secret not captured")


def test_capture_secret_registered_vault_factory_offers_and_stores_in_vault(tmp_path: Path) -> None:
    vault = _MemoryVault("team-vault")
    registry = VaultRegistry().register(_MemoryVaultFactory(vault))
    options = VaultOptions(name="team-vault", kind="memory-vault")
    user = _ScriptedInput(SECRET, provider="team-vault")
    service = _service(tmp_path, KeyringInMemory(), user, registry, options)

    captured = service.capture("communication", "slack", preferred_provider="team-vault")

    assert isinstance(captured, Ok) and captured.value.provider == "team-vault"
    assert user.requests[0].available_providers == ["aesLocal", "literal", "team-vault"]
    assert vault.values == {"communication.slack": SECRET}
    assert SECRET not in _disk(tmp_path)


def test_create_unregistered_vault_kind_fails_validation(tmp_path: Path, log_capture: LogCapture) -> None:
    options = _options(tmp_path, VaultOptions(name="v", kind="azure-key-vault"))

    created = SecretCaptureService.create(options, VaultRegistry.default(), KeyringInMemory())

    assert isinstance(created, Err)
    assert created.category == "Validation" and "azure-key-vault" in created.message
    assert log_capture.records[-1][0] == "error"


def test_vault_registry_default_registers_bitwarden_kinds() -> None:
    registry = VaultRegistry.default()

    assert registry.kinds() == ("bitwarden-secrets", "bws", "bitwarden")
    assert isinstance(registry.find("bws"), Ok)
    assert isinstance(registry.find("azure-key-vault"), Err)


def test_secret_resolver_reads_secret_through_registered_vault(tmp_path: Path) -> None:
    vault = _MemoryVault("team-vault")
    registry = VaultRegistry().register(_MemoryVaultFactory(vault))
    options = VaultOptions(name="team-vault", kind="memory-vault")
    keyring = KeyringInMemory()
    user = _ScriptedInput(SECRET, provider="team-vault")
    _service(tmp_path, keyring, user, registry, options).capture("communication", "slack")

    resolver = SecretResolver.create(
        APP,
        str(tmp_path / "config"),
        keyring,
        {},
        str(tmp_path / "manifest.json"),
        options,
        registry,
    )

    assert isinstance(resolver, Ok)
    resolved = resolver.value.resolve("communication", "slack")
    assert isinstance(resolved, Ok) and resolved.value.reveal() == SECRET


def test_capture_secret_loopback_page_stores_posted_secret(tmp_path: Path) -> None:
    status = io.StringIO()
    loopback = LoopbackSecretInputProvider(_NoBrowser(), status)

    def submit() -> None:
        url = loopback.wait_for_url()
        assert url is not None
        body = urllib.parse.urlencode(
            {
                "session_token": loopback.session_token,
                "secret": SECRET,
                "confirm_secret": SECRET,
                "provider": "aesLocal",
            }
        ).encode()
        with urllib.request.urlopen(urllib.request.Request(url, data=body, method="POST"), timeout=5) as response:
            response.read()

    browser = threading.Thread(target=submit)
    browser.start()
    created = SecretCaptureService.create(_options(tmp_path), None, KeyringInMemory(), loopback)
    assert isinstance(created, Ok)

    captured = created.value.capture("vault", "bws-access-token", mode=SecretCaptureMode.WEB, timeout_seconds=10)
    browser.join(timeout=10)

    assert isinstance(captured, Ok) and captured.value.provider == "aesLocal"
    assert "127.0.0.1" in status.getvalue() and SECRET not in status.getvalue()
    assert SECRET not in _disk(tmp_path)


@dataclass
class _NoBrowser:
    def open_url(self, url: str) -> Result[None]:
        return ok(None)
