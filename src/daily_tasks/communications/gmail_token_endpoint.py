"""Responsibility: Post OAuth token requests to Google and reject grants wider than Gmail read-only.
Public interface:
`-- GmailTokenEndpoint
    +-- new(client_secret, http_post)
    `-- post(url, form_data)

`OAuthFlowClient` transport for Google: adds the client secret, enforces the granted scope.
"""

import json
import urllib.error
import urllib.parse
import urllib.request
from collections.abc import Callable, Mapping
from typing import Final, final

from nyssa_ai_result import Result, fail, ok

from daily_tasks.communications.gmail_readonly_scope import GMAIL_READONLY_SCOPE
from daily_tasks.communications.secret_string import SecretString

type _HttpPost = Callable[[str, Mapping[str, str]], Result[tuple[int, str]]]

_TIMEOUT_SECONDS: Final = 15.0


@final
class GmailTokenEndpoint:
    """Pass as `OAuthFlowClient(http_post=endpoint.post)`; the client secret stays in memory.

    Google desktop clients require `client_secret` on code exchange and refresh. A successful token
    response whose `scope` is not exactly `gmail.readonly` fails with `Forbidden` before the grant can
    be sealed or used.
    """

    def __init__(self, client_secret: SecretString | None, http_post: _HttpPost | None = None) -> None:
        """`client_secret=None` omits it (PKCE-only clients); `http_post=None` uses `urllib`."""
        self._client_secret = client_secret
        self._http_post: _HttpPost = http_post if http_post is not None else _urllib_post

    def post(self, url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]:
        """Return `(status, body)` from the token endpoint, or `Forbidden` for a non-read-only grant."""
        form = dict(form_data)
        if self._client_secret is not None:
            form["client_secret"] = self._client_secret.reveal()
        response = self._http_post(url, form)
        if not response.ok:
            return response
        status, body = response.value
        if 200 <= status < 300:
            granted = _granted_scope(body)
            if granted is not None and granted.split() != [GMAIL_READONLY_SCOPE]:
                return fail("Google granted a scope other than gmail.readonly; access refused.", "Forbidden")
        return response


def _granted_scope(body: str) -> str | None:
    try:
        payload: object = json.loads(body)
    except ValueError:
        return None
    if isinstance(payload, dict):
        scope = payload.get("scope")
        return scope if isinstance(scope, str) else None
    return None


def _urllib_post(url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]:
    request = urllib.request.Request(
        url,
        data=urllib.parse.urlencode(form_data).encode("utf-8"),
        headers={"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=_TIMEOUT_SECONDS) as response:
            return ok((int(response.status), response.read().decode("utf-8")))
    except urllib.error.HTTPError as exc:
        return ok((int(exc.code), exc.read().decode("utf-8", errors="replace")))
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return fail("Google token endpoint is unreachable.", "Unavailable", cause=exc)
