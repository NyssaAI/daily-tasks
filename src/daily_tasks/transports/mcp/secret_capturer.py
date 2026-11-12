"""Responsibility: Define the role-named SecretCapturer contract for out-of-band MCP secret capture.
Public interface:
`-- SecretCapturer
    `-- capture_secret(namespace, key, prompt_message, provider)
"""

from typing import Protocol

from pydantic import JsonValue


class SecretCapturer(Protocol):
    """Capture a secret out-of-band and return a sanitized receipt body."""

    async def capture_secret(
        self,
        namespace: str,
        key: str,
        prompt_message: str | None = None,
        provider: str | None = None,
    ) -> dict[str, JsonValue]:
        """Prompt the user out-of-band and return the structured receipt reply."""
        ...
