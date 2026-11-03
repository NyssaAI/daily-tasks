# Responsibility: Resolve adapter secrets into memory from the environment or the keyring-protected configuration.
# Public interface:
# `-- SecretResolver
#     +-- create(application_name, configuration_directory, logger, keyring, environ, manifest_path)
#     +-- new(reader, logger, environ)
#     `-- resolve(namespace, key, env_var)
"""Runtime secret resolution: plaintext stays in process memory inside a `SecretString`."""

import os
import time
from collections.abc import Mapping
from typing import final

from nyssa_ai_configuration import BootstrapOptions, ConfigurationClient, ConfigurationReader, Keyring
from nyssa_ai_result import Result, fail, ok

from daily_tasks.credentials.secret_logger import SecretLogger
from daily_tasks.domain.secret_string import SecretString

_OPERATION = "secrets.resolve"


@final
class SecretResolver:
    """Resolve a secret from `env_var` first, else from the `aesLocal`/vault entry at (namespace, key).

    Values sealed in the configuration store are encrypted with the master key the keyring holds,
    so no plaintext credential file is read or written.
    """

    def __init__(self, reader: ConfigurationReader, logger: SecretLogger, environ: Mapping[str, str]) -> None:
        """Borrow `reader` and `logger`; `environ` is the environment snapshot to read tokens from."""
        self._reader = reader
        self._logger = logger
        self._environ = environ

    @classmethod
    def create(
        cls,
        application_name: str,
        configuration_directory: str,
        logger: SecretLogger,
        keyring: Keyring | None = None,
        environ: Mapping[str, str] | None = None,
        manifest_path: str | None = None,
    ) -> Result["SecretResolver"]:
        """Open the configuration store; `keyring=None` lets the library pick `KeyringDefault` on desktops.

        Pass `KeyringInMemory` for tests; `environ=None` reads `os.environ`.
        Fails with the configuration bootstrap error.
        """
        options = BootstrapOptions(
            application_name=application_name,
            configuration_directory=configuration_directory,
            manifest_path=manifest_path,
        )
        client = ConfigurationClient.create(options, keyring=keyring)
        if not client.ok:
            logger.error("secret store unavailable", fields={"category": str(client.category)}, operation=_OPERATION)
            return client
        return ok(cls(client.value, logger, environ if environ is not None else os.environ))

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
        self._logger.debug("secret resolved", fields=fields, operation=_OPERATION)

    def _log_missing(self, namespace: str, key: str, category: str, started: float) -> None:
        fields = {"namespace": namespace, "key": key, "category": category, "elapsed_ms": _elapsed_ms(started)}
        self._logger.warn("secret not resolved", fields=fields, operation=_OPERATION)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
