"""Responsibility: Run the out-of-band secret capture tool and reply with only the sanitized receipt.
Public interface:
`-- SecretTools
    +-- TOOL
    +-- capture_secret(namespace, key, prompt_message, provider)
    `-- new(open_service, timeout_seconds)

`daily_tasks_capture_secret`: the user types the secret into a loopback browser page, never into the chat.
"""

import asyncio
import logging
import time
from collections.abc import Callable
from typing import ClassVar, Final, final

from nyssa_ai_configuration import SecretCaptureMode
from nyssa_ai_result import Result
from pydantic import JsonValue, TypeAdapter

from daily_tasks.credentials import SecretCaptureService, secret_receipt_fields
from daily_tasks.domain import ToolResultError

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "mcp.capture_secret"
_ERROR: Final[TypeAdapter[ToolResultError]] = TypeAdapter(ToolResultError)


@final
class SecretTools:
    """Open the configuration store per call and capture through the loopback page (`WEB` mode).

    Stdin carries JSON-RPC, so terminal input is never used; the loopback URL goes to stderr and the browser.
    Replies hold `namespace`, `key`, `provider` and `stored_at`; the secret itself never reaches the agent.
    """

    TOOL: ClassVar[str] = "daily_tasks_capture_secret"

    def __init__(
        self,
        open_service: Callable[[], Result[SecretCaptureService]],
        timeout_seconds: float = 300.0,
    ) -> None:
        """Keep `open_service`, called once per capture, and the loopback wait in seconds."""
        self._open_service = open_service
        self._timeout_seconds = timeout_seconds

    async def capture_secret(
        self, namespace: str, key: str, prompt_message: str | None = None, provider: str | None = None
    ) -> dict[str, JsonValue]:
        """Wait for the user to submit the loopback form, then return an `ok` body with the receipt as payload.

        `provider` preselects the storage provider; the user may still choose another available one.
        Failures (store unavailable, timeout, cancelled or mismatched entry) return an `error` body.
        """
        started = time.monotonic()
        service = self._open_service()
        if not service.ok:
            return self._failed(service.message, str(service.category), started)
        captured = await asyncio.to_thread(
            service.value.capture,
            namespace,
            key,
            prompt_message,
            provider,
            None,
            SecretCaptureMode.WEB,
            self._timeout_seconds,
        )
        if not captured.ok:
            return self._failed(captured.message, str(captured.category), started)
        receipt = secret_receipt_fields(captured.value)
        fields: dict[str, object] = {**receipt, "outcome": "ok", "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.info("secret captured", extra={"operation": _OPERATION, "fields": fields})
        payload: dict[str, JsonValue] = {"receipt": dict(receipt)}
        message = f"Stored {receipt['namespace']}/{receipt['key']} in {receipt['provider']}."
        return {"tool": self.TOOL, "status": "ok", "message": message, "payload": payload}

    def _failed(self, message: str, code: str, started: float) -> dict[str, JsonValue]:
        fields = {"code": code, "outcome": "error", "elapsed_ms": _elapsed_ms(started)}
        _LOGGER.warning("secret not captured", extra={"operation": _OPERATION, "fields": fields})
        result = ToolResultError(
            tool=self.TOOL,
            status="error",
            session_id=None,
            screen_id=None,
            stage=None,
            message=message,
            code=code,
            payload=None,
        )
        dumped: dict[str, JsonValue] = _ERROR.dump_python(result, mode="json")
        return dumped


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
