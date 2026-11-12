"""Responsibility: Resolve connector secrets into memory from the environment or the keyring-protected configuration.
Public interface:
`-- SecretResolver
    +-- create(application_name, configuration_directory, keyring, environ, manifest_path, vault, vaults)
    +-- new(reader, environ)
    `-- resolve(namespace, key, env_var)
"""

import logging
import os
import time
from collections.abc import Mapping
from typing import Final, final

from nyssa_ai_configuration import BootstrapOptions, ConfigurationClient, ConfigurationReader, Keyring, VaultOptions
from nyssa_ai_result import Result, fail, ok

from daily_tasks.communications.secret_string import SecretString
from daily_tasks.communications.vault_registry import VaultRegistry

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION = "secrets.resolve"


@final
class SecretResolver:
    """Resolve a secret from `env_var` first, else from the `aesLocal`/vault entry at (namespace, key)."""

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
        """Open the configuration store; `keyring=None` lets the library pick `KeyringDefault` on desktops."""
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
        """Return the secret, never its value in errors or logs."""
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
