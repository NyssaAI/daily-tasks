"""Responsibility: Capture a secret out-of-band through the configuration store and log only its sanitized receipt.
Public interface:
`-- SecretCaptureService
    +-- capture(namespace, key, prompt_message, preferred_provider, forced_provider, mode, timeout_seconds)
    +-- create(options, vaults, keyring, input_provider, status_out)
    `-- new(writer, input_provider, status_out)

`ConfigurationClient.capture_secret()` wrapper: the plaintext goes from the user to storage, never to the caller.
"""

import logging
import sys
import time
from typing import Final, TextIO, final

from nyssa_ai_configuration import (
    AdaptiveSecretInputProvider,
    BootstrapOptions,
    CaptureSecretOptions,
    ConfigurationClient,
    ConfigurationSecretWriter,
    Keyring,
    SecretCaptureMode,
    SecretInputProvider,
    SecretReceipt,
)
from nyssa_ai_result import Result, fail, ok

from daily_tasks.credentials.secret_receipt_fields import secret_receipt_fields
from daily_tasks.credentials.vault_registry import VaultRegistry

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "secrets.capture"


@final
class SecretCaptureService:
    """Prompt the user in the terminal (masked) or a loopback browser page, then store the secret.

    Results and log records carry only the `SecretReceipt` (namespace, key, provider, stored_at).
    Status text such as the loopback URL goes to `status_out` (stderr by default), never stdout.
    """

    def __init__(
        self,
        writer: ConfigurationSecretWriter,
        input_provider: SecretInputProvider | None = None,
        status_out: TextIO | None = None,
    ) -> None:
        """Borrow `writer`; `input_provider=None` picks CLI or loopback input per capture `mode`."""
        self._writer = writer
        self._input_provider = input_provider
        self._status_out = status_out if status_out is not None else sys.stderr

    @classmethod
    def create(
        cls,
        options: BootstrapOptions,
        vaults: VaultRegistry | None = None,
        keyring: Keyring | None = None,
        input_provider: SecretInputProvider | None = None,
        status_out: TextIO | None = None,
    ) -> Result["SecretCaptureService"]:
        """Open the configuration store with every factory of `vaults` (default: `VaultRegistry.default()`).

        `options.key_vault` applies only when the manifest has no vault for the application yet.
        Fails with the configuration bootstrap error, or `Validation` for an unregistered vault kind.
        """
        registry = vaults if vaults is not None else VaultRegistry.default()
        if options.key_vault is not None:
            found = registry.find(options.key_vault.kind)
            if not found.ok:
                _LOGGER.error(
                    "secret store unavailable",
                    extra={"operation": _OPERATION, "fields": {"category": "Validation"}},
                )
                return fail(found.message, found.category)
        client = ConfigurationClient.create(options, keyring=keyring, vault_factories=registry.factories())
        if not client.ok:
            _LOGGER.error(
                "secret store unavailable",
                extra={"operation": _OPERATION, "fields": {"category": str(client.category)}},
            )
            return client
        return ok(cls(client.value, input_provider, status_out))

    def capture(
        self,
        namespace: str,
        key: str,
        prompt_message: str | None = None,
        preferred_provider: str | None = None,
        forced_provider: str | None = None,
        mode: SecretCaptureMode = SecretCaptureMode.AUTO,
        timeout_seconds: float = 120.0,
    ) -> Result[SecretReceipt]:
        """Prompt for the secret at (namespace, key), store it and return its receipt.

        The store offers `aesLocal`, `literal` and every configured vault (`get_available_secret_providers()`);
        `forced_provider` pins one of them, `preferred_provider` only preselects it.

        `AUTO` uses masked terminal input on a TTY and the loopback page otherwise. Fails with
        `Validation` (unknown provider, mismatched or cancelled entry), `Unavailable` (timeout) or the store's error.
        """
        started = time.monotonic()
        provider = self._input_provider or AdaptiveSecretInputProvider(mode, stream_out=self._status_out)
        options = CaptureSecretOptions(
            prompt_message=prompt_message,
            preferred_provider=preferred_provider,
            forced_provider=forced_provider,
            mode=mode,
            timeout_seconds=timeout_seconds,
            input_provider=provider,
        )
        captured = self._writer.capture_secret(namespace, key, options)
        elapsed_ms = round((time.monotonic() - started) * 1000, 3)
        if not captured.ok:
            fields = {"namespace": namespace, "key": key, "category": str(captured.category), "elapsed_ms": elapsed_ms}
            _LOGGER.warning("secret not captured", extra={"operation": _OPERATION, "fields": fields})
            return captured
        receipt_fields: dict[str, object] = {**secret_receipt_fields(captured.value), "elapsed_ms": elapsed_ms}
        _LOGGER.debug("secret captured", extra={"operation": _OPERATION, "fields": receipt_fields})
        return captured
