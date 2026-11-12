"""Responsibility: Define the HTTP GET the Gmail connector needs from its transport.
Public interface:
`-- GmailHttp
    `-- get(url, headers, timeout_seconds)

Narrow transport contract so the Gmail connector runs offline in tests.
"""

from collections.abc import Mapping
from typing import Protocol

from nyssa_ai_result import Result


class GmailHttp(Protocol):
    """Blocking HTTPS GET; the connector runs it in a worker thread."""

    def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]:
        """Return the response body of a successful (2xx) response.

        Fails with `Unavailable` when the host cannot be reached, times out or answers with a non-2xx
        status; the message names the status (`http_401`) and never contains header values.
        """
        ...
