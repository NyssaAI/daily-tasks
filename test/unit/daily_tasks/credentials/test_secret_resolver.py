# Responsibility: Prove SecretResolver resolves secrets into memory without leaking them to disk or logs.
# Public interface:
# (none)
"""Secret resolution through the environment and a keyring-protected configuration store."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from nyssa_ai_configuration import BootstrapOptions, ConfigurationClient, KeyringInMemory
from nyssa_ai_result import Err, Ok

from daily_tasks.credentials import SecretResolver

APP = "daily-tasks-test"
TOKEN = "xoxb-live-token-123"


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


def _seal_token(root: Path, keyring: KeyringInMemory) -> None:
    options = BootstrapOptions(
        application_name=APP, configuration_directory=str(root / "config"), manifest_path=str(root / "manifest.json")
    )
    client = ConfigurationClient.create(options, keyring=keyring)
    assert isinstance(client, Ok)
    assert client.value.set("communication", "slack", TOKEN, "aesLocal").ok


def _resolver(
    root: Path, keyring: KeyringInMemory, logger: _RecordingLogger, environ: Mapping[str, str]
) -> SecretResolver:
    created = SecretResolver.create(
        APP, str(root / "config"), logger, keyring=keyring, environ=environ, manifest_path=str(root / "manifest.json")
    )
    assert isinstance(created, Ok)
    return created.value


def test_secret_resolver_keyring_sealed_secret_resolves_without_plaintext_on_disk(tmp_path: Path) -> None:
    keyring = KeyringInMemory()
    _seal_token(tmp_path, keyring)
    logger = _RecordingLogger()

    result = _resolver(tmp_path, keyring, logger, {}).resolve("communication", "slack", "SLACK_TOKEN")

    assert isinstance(result, Ok)
    assert result.value.reveal() == TOKEN
    assert all(TOKEN not in path.read_text(encoding="utf-8") for path in tmp_path.rglob("*") if path.is_file())
    assert TOKEN not in repr(logger.records)
    assert logger.records[-1][2]["source"] == "configuration"


def test_secret_resolver_environment_variable_takes_precedence(tmp_path: Path) -> None:
    keyring = KeyringInMemory()
    _seal_token(tmp_path, keyring)
    logger = _RecordingLogger()

    result = _resolver(tmp_path, keyring, logger, {"SLACK_TOKEN": "from-env"}).resolve(
        "communication", "slack", "SLACK_TOKEN"
    )

    assert isinstance(result, Ok)
    assert result.value.reveal() == "from-env"
    assert logger.records[-1][2]["source"] == "environment"


def test_secret_resolver_missing_secret_fails_not_found(tmp_path: Path) -> None:
    logger = _RecordingLogger()

    result = _resolver(tmp_path, KeyringInMemory(), logger, {}).resolve("communication", "gmail", "GMAIL_TOKEN")

    assert isinstance(result, Err)
    assert result.category == "NotFound"
    assert logger.records[-1][0:2] == ("warn", "secret not resolved")


def test_secret_resolver_different_master_key_cannot_read_sealed_secret(tmp_path: Path) -> None:
    _seal_token(tmp_path, KeyringInMemory())

    result = _resolver(tmp_path, KeyringInMemory(), _RecordingLogger(), {}).resolve("communication", "slack")

    assert isinstance(result, Err)


def test_secret_resolver_keyring_read_failure_fails_create(tmp_path: Path) -> None:
    logger = _RecordingLogger()

    created = SecretResolver.create(
        APP,
        str(tmp_path / "config"),
        logger,
        keyring=KeyringInMemory(fail_on_read=True),
        manifest_path=str(tmp_path / "manifest.json"),
    )

    assert isinstance(created, Err)
    assert logger.records[-1][0] == "error"
