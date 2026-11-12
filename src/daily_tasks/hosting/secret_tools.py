"""Responsibility: Expose out-of-band secret capture to the MCP transport without leaking secret values.
Public interface:
`-- SecretTools
    +-- TOOL
    +-- capture_secret(namespace, key, prompt_message, provider)
    `-- new(open_service)
"""

import asyncio
import logging
from collections.abc import Callable
from typing import ClassVar, Final, final

from nyssa_ai_configuration import SecretCaptureMode
from nyssa_ai_result import Result
from pydantic import JsonValue, TypeAdapter

from daily_tasks.communications.secret_capture_service import SecretCaptureService
from daily_tasks.communications.secret_receipt_fields import secret_receipt_fields
from daily_tasks.core.planning.tool_result_error import ToolResultError

_LOGGER: Final = logging.getLogger(__name__)
_OPERATION: Final = "mcp.secret"
_ERROR: Final[TypeAdapter[ToolResultError]] = TypeAdapter(ToolResultError)


@final
class SecretTools:
    """Entity-first `SecretCapturer` opening a loopback browser prompt so secrets bypass chat context."""

    TOOL: ClassVar[str] = "daily_tasks_capture_secret"

    def __init__(self, open_service: Callable[[], Result[SecretCaptureService]]) -> None:
        """`open_service` opens the user-home configuration client lazily."""
        self._open_service = open_service

    async def capture_secret(
        self,
        namespace: str,
        key: str,
        prompt_message: str | None = None,
        provider: str | None = None,
    ) -> dict[str, JsonValue]:
        """Prompt the user in a browser window (`WEB`) and return a sanitized receipt."""
        opened = self._open_service()
        if not opened.ok:
            return self._failed(opened.message, str(opened.category))
        captured = await asyncio.to_thread(
            opened.value.capture,
            namespace,
            key,
            prompt_message=prompt_message,
            preferred_provider=provider,
            mode=SecretCaptureMode.WEB,
        )
        if not captured.ok:
            return self._failed(captured.message, str(captured.category))
        receipt = secret_receipt_fields(captured.value)
        _LOGGER.info("secret captured", extra={"operation": _OPERATION, "fields": {"provider": receipt["provider"]}})
        payload: dict[str, JsonValue] = {
            "namespace": receipt["namespace"],
            "key": receipt["key"],
            "provider": receipt["provider"],
            "stored_at": receipt["stored_at"],
        }
        return {"tool": self.TOOL, "status": "ok", "message": "Secret stored out of band.", "payload": payload}

    def _failed(self, message: str, category: str) -> dict[str, JsonValue]:
        _LOGGER.warning("secret not captured", extra={"operation": _OPERATION, "fields": {"code": category}})
        error = ToolResultError(
            tool=self.TOOL,
            status="error",
            session_id=None,
            screen_id=None,
            stage=None,
            message=message,
            code=category,
            payload=None,
        )
        body: dict[str, JsonValue] = _ERROR.dump_python(error, mode="json")
        return body
