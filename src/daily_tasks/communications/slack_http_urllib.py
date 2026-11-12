"""Responsibility: Perform Slack Web API GET requests with the standard library.
Public interface:
`-- SlackHttpUrllib
    `-- get(url, headers, timeout_seconds)

Default `SlackHttp` transport over `urllib.request`; no third-party HTTP client is required.
"""

import urllib.error
import urllib.request
from collections.abc import Mapping
from typing import final

from nyssa_ai_result import Result, fail, ok


@final
class SlackHttpUrllib:
    """Stateless transport; each call opens and closes its own connection."""

    def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]:
        """GET `url`; fails with `Unavailable` and `http_<status>` or `network_error` (never header values)."""
        request = urllib.request.Request(url, headers=dict(headers), method="GET")
        try:
            with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
                body: bytes = response.read()
                return ok(body)
        except urllib.error.HTTPError as exc:
            return fail(f"http_{exc.code}", "Unavailable", cause=exc)
        except (urllib.error.URLError, TimeoutError, OSError) as exc:
            return fail("network_error", "Unavailable", cause=exc)
