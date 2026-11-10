"""Responsibility: Resolve adapter secrets into memory from the environment or the keyring-protected configuration.
Public interface:
`-- SecretResolver
    +-- create(application_name, configuration_directory, keyring, environ, manifest_path, vault, vaults)
    +-- new(reader, environ)
    `-- resolve(namespace, key, env_var)

Runtime secret resolution: plaintext stays in process memory inside a `SecretString`.
"""

import logging
import os
import time
from collections.abc import Mapping
from typing import Final, final

from nyssa_ai_configuration import BootstrapOptions, ConfigurationClient, ConfigurationReader, Keyring, VaultOptions
from nyssa_ai_result import Result, fail, ok

from daily_tasks.credentials.vault_registry import VaultRegistry
from daily_tasks.domain.secret_string import SecretString

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "secrets.resolve"


@final
class SecretResolver:
    """Resolve a secret from `env_var` first, else from the `aesLocal`/vault entry at (namespace, key).

    Values sealed in the configuration store are encrypted with the master key the keyring holds,
    so no plaintext credential file is read or written.
    """

    def __init__(self, reader: ConfigurationReader, environ: Mapping[str, str]) -> None:
        """Borrow `reader`; `environ` is the environment snapshot to read tokens from."""
        self._reader = reader
        self._environ = environ

    @classmethod
    def create(
        cls,
        application_name: str,
        configuration_directory: str,
        keyring: Keyring | None = None,
        environ: Mapping[str, str] | None = None,
        manifest_path: str | None = None,
        vault: VaultOptions | None = None,
        vaults: VaultRegistry | None = None,
    ) -> Result["SecretResolver"]:
        """Open the configuration store; `keyring=None` lets the library pick `KeyringDefault` on desktops.

        Pass `KeyringInMemory` for tests; `environ=None` reads `os.environ`. Vault entries resolve through the
        factories of `vaults` (default: `VaultRegistry.default()`); `vault` applies only when the
        manifest has no vault for the application yet.
        Fails with the configuration bootstrap error.
        """
        registry = vaults if vaults is not None else VaultRegistry.default()
        options = BootstrapOptions(
            application_name=application_name,
            configuration_directory=configuration_directory,
            manifest_path=manifest_path,
            key_vault=vault,
        )
        client = ConfigurationClient.create(options, keyring=keyring, vault_factories=registry.factories())
        if not client.ok:
            _LOGGER.error(
                "secret store unavailable",
                extra={"operation": _OPERATION, "fields": {"category": str(client.category)}},
            )
            return client
        return ok(cls(client.value, environ if environ is not None else os.environ))

    def resolve(self, namespace: str, key: str, env_var: str | None = None) -> Result[SecretString]:
        """Return the secret, never its value in errors or logs.

        Fails with `NotFound` when neither source has a non-empty value, or the store's error category.
        """
        started = time.monotonic()
        from_env = self._environ.get(env_var, "") if env_var else ""
        if from_env:
            self._log_resolved(namespace, key, "environment", started)
            return ok(SecretString(from_env))
        stored = self._reader.get(namespace, key)
        if not stored.ok:
            self._log_missing(namespace, key, str(stored.category), started)
            return fail(f"Secret '{namespace}/{key}' is not available.", stored.category)
        if not stored.value:
            self._log_missing(namespace, key, "NotFound", started)
            return fail(f"Secret '{namespace}/{key}' is empty.", "NotFound")
        self._log_resolved(namespace, key, "configuration", started)
        return ok(SecretString(stored.value))

    def _log_resolved(self, namespace: str, key: str, source: str, started: float) -> None:
        fields = {"namespace": namespace, "key": key, "source": source, "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.debug("secret resolved", extra={"operation": _OPERATION, "fields": fields})

    def _log_missing(self, namespace: str, key: str, category: str, started: float) -> None:
        fields = {"namespace": namespace, "key": key, "category": category, "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.warning("secret not resolved", extra={"operation": _OPERATION, "fields": fields})


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
