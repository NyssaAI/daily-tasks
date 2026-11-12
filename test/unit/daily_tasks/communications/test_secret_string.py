"""Responsibility: Prove SecretString never leaks its value through text, logs, or JSON dumps.
Public interface:
+-- TOKEN
+-- test_disk_credential_fields_are_deprecated_in_schema(record_cls, field)
+-- test_port_config_without_credentials_root_validates()
+-- test_secret_string_empty_value_raises()
+-- test_secret_string_in_container_repr_is_redacted()
+-- test_secret_string_is_immutable_and_copies_as_itself()
+-- test_secret_string_json_dump_without_reveal_is_redacted()
+-- test_secret_string_log_record_is_redacted(caplog)
+-- test_secret_string_pickle_is_refused()
+-- test_secret_string_plain_json_dumps_refuses_value()
+-- test_secret_string_reveal_returns_value()
`-- test_secret_string_text_rendering_is_redacted(render)

SecretString redaction and the deprecated disk credential fields on `PortConfig` and `CommunicationBinding`.
"""

import copy
import json
import logging
import pickle
import warnings

import pytest
from pydantic import TypeAdapter
from pydantic.dataclasses import dataclass

from conftest import load_spec
from daily_tasks.communications import SecretString
from daily_tasks.core.planning import CommunicationBinding, PortConfig

TOKEN = "xoxb-live-token-123"


@dataclass(frozen=True)
class _Binding:
    name: str
    token: SecretString


def test_secret_string_reveal_returns_value() -> None:
    assert SecretString(TOKEN).reveal() == TOKEN


@pytest.mark.parametrize("render", [str, repr, "{}".format, "{!r}".format, lambda s: f"{s}"])
def test_secret_string_text_rendering_is_redacted(render: object) -> None:
    assert callable(render)
    text = render(SecretString(TOKEN))

    assert TOKEN not in text
    assert "[REDACTED]" in text


def test_secret_string_in_container_repr_is_redacted() -> None:
    text = repr({"token": SecretString(TOKEN), "items": [SecretString(TOKEN)]})

    assert TOKEN not in text


def test_secret_string_log_record_is_redacted(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("daily_tasks.test")

    with caplog.at_level(logging.INFO, logger="daily_tasks.test"):
        logger.info("token %s in %r", SecretString(TOKEN), {"token": SecretString(TOKEN)})

    assert TOKEN not in caplog.text
    assert "[REDACTED]" in caplog.text


def test_secret_string_json_dump_without_reveal_is_redacted() -> None:
    adapter = TypeAdapter(_Binding)
    binding = adapter.validate_python({"name": "slack", "token": TOKEN})

    dumped = adapter.dump_json(binding).decode()

    assert TOKEN not in dumped
    assert json.loads(dumped) == {"name": "slack", "token": "[REDACTED]"}
    assert binding.token.reveal() == TOKEN


def test_secret_string_plain_json_dumps_refuses_value() -> None:
    with pytest.raises(TypeError):
        json.dumps({"token": SecretString(TOKEN)})


def test_secret_string_pickle_is_refused() -> None:
    with pytest.raises(TypeError):
        pickle.dumps(SecretString(TOKEN))


def test_secret_string_is_immutable_and_copies_as_itself() -> None:
    secret = SecretString(TOKEN)

    with pytest.raises(AttributeError):
        secret._value = "other"
    assert copy.deepcopy(secret) is secret
    assert secret == SecretString(TOKEN)
    assert secret != SecretString("other")


def test_secret_string_empty_value_raises() -> None:
    with pytest.raises(ValueError):
        SecretString("")


def test_port_config_without_credentials_root_validates() -> None:
    spec = load_spec("port-config.json")
    assert isinstance(spec, dict)
    spec.pop("credentials_root", None)

    config = TypeAdapter(PortConfig).validate_python(spec)

    assert "credentials_root" not in TypeAdapter(PortConfig).dump_python(config, exclude_unset=True)


@pytest.mark.parametrize(
    ("record_cls", "field"), [(PortConfig, "credentials_root"), (CommunicationBinding, "credentials_file")]
)
def test_disk_credential_fields_are_deprecated_in_schema(record_cls: type[object], field: str) -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        schema = TypeAdapter(record_cls).json_schema()

    assert schema["properties"][field]["deprecated"] is True
