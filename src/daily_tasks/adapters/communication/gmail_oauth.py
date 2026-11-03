# Responsibility: Sign in to Gmail read-only and hand out sealed, headlessly refreshed access tokens.
# Public interface:
# `-- GmailOauth
#     +-- DEFAULT_KEY
#     +-- DEFAULT_NAMESPACE
#     +-- access_token()
#     +-- authorize(scopes)
#     +-- create(options, client_id, client_secret, logger, keyring, http_post, now, browser_launcher)
#     `-- new(store, client_id, logger, browser_launcher, namespace, key)
"""Gmail OAuth 2.0 (PKCE loopback) over `nyssa_ai_configuration`; grants are only ever stored sealed."""

import time
from collections.abc import Callable, Mapping, Sequence
from datetime import UTC, datetime
from typing import ClassVar, Final, final

from nyssa_ai_configuration import (
    BootstrapOptions,
    BrowserLauncher,
    ConfigurationClient,
    Keyring,
    OAuthFlowClient,
    OAuthOptions,
)
from nyssa_ai_result import Result, fail, ok

from daily_tasks.adapters.communication.gmail_readonly_scope import (
    GMAIL_READONLY_SCOPE,
    GOOGLE_AUTHORIZATION_ENDPOINT,
    GOOGLE_TOKEN_ENDPOINT,
)
from daily_tasks.adapters.communication.gmail_token_endpoint import GmailTokenEndpoint
from daily_tasks.adapters.communication.gmail_token_store import GmailTokenStore
from daily_tasks.domain import SecretString
from daily_tasks.ports import PortLogger

_AUTHORIZE: Final = "gmail.oauth.authorize"
_ACCESS_TOKEN: Final = "gmail.oauth.access_token"


@final
class GmailOauth:
    """Owns the Gmail grant at (namespace, key) in the keyring-protected configuration store.

    The grant (access + refresh token) is sealed with the keyring-held master key before it touches
    disk; tokens never appear in `repr`, errors or logs. Reads refresh a grant expiring within five
    minutes without a browser; a revoked refresh token fails with `Forbidden` until `authorize` runs.
    """

    DEFAULT_NAMESPACE: ClassVar[str] = "communication"
    DEFAULT_KEY: ClassVar[str] = "gmail-oauth"

    def __init__(
        self,
        store: GmailTokenStore,
        client_id: SecretString,
        logger: PortLogger,
        browser_launcher: BrowserLauncher | None = None,
        namespace: str = DEFAULT_NAMESPACE,
        key: str = DEFAULT_KEY,
    ) -> None:
        """Borrow `store` and `logger`; `browser_launcher=None` opens the system browser."""
        self._store = store
        self._client_id = client_id
        self._logger = logger
        self._browser_launcher = browser_launcher
        self._namespace = namespace
        self._key = key

    @classmethod
    def create(
        cls,
        options: BootstrapOptions,
        client_id: SecretString,
        client_secret: SecretString | None,
        logger: PortLogger,
        keyring: Keyring | None = None,
        http_post: Callable[[str, Mapping[str, str]], Result[tuple[int, str]]] | None = None,
        now: Callable[[], datetime] | None = None,
        browser_launcher: BrowserLauncher | None = None,
    ) -> Result["GmailOauth"]:
        """Open the configuration store described by `options`, wired to Google's token endpoint.

        `keyring=None` lets the library pick `KeyringDefault`; pass `KeyringInMemory` in tests.
        `http_post=None` posts with `urllib`; `now=None` uses the UTC wall clock.
        Fails with the configuration bootstrap error.
        """
        endpoint = GmailTokenEndpoint(client_secret, http_post)
        flow = OAuthFlowClient(http_post=endpoint.post, now=now if now is not None else _utc_now)
        client = ConfigurationClient.create(options, keyring=keyring, oauth_flow_client=flow)
        if not client.ok:
            logger.error(
                "gmail token store unavailable", fields={"category": str(client.category)}, operation=_AUTHORIZE
            )
            return client
        return ok(cls(client.value, client_id, logger, browser_launcher))

    def authorize(self, scopes: Sequence[str] = (GMAIL_READONLY_SCOPE,)) -> Result[None]:
        """Run the interactive PKCE sign-in and seal the grant.

        Fails with `Validation` unless `scopes` is exactly `gmail.readonly`, `Forbidden` when the user
        denies access or Google grants another scope, else the flow's or store's error category.
        """
        started = time.monotonic()
        if tuple(scopes) != (GMAIL_READONLY_SCOPE,):
            self._log_failed(_AUTHORIZE, "Validation", started)
            return fail(f"Gmail access is limited to the '{GMAIL_READONLY_SCOPE}' scope.", "Validation")
        options = OAuthOptions(
            authorization_endpoint=GOOGLE_AUTHORIZATION_ENDPOINT,
            token_endpoint=GOOGLE_TOKEN_ENDPOINT,
            client_id=self._client_id.reveal(),
            scopes=(GMAIL_READONLY_SCOPE,),
        )
        stored = self._store.authorize(self._namespace, self._key, options, self._browser_launcher)
        if not stored.ok:
            self._log_failed(_AUTHORIZE, str(stored.category), started)
            return fail(stored.message, stored.category)
        self._logger.info("gmail authorized", fields=self._fields(started), operation=_AUTHORIZE)
        return ok(None)

    def access_token(self) -> Result[SecretString]:
        """Return a valid access token, refreshing it headlessly when it expires within five minutes.

        Fails with `NotFound` before the first sign-in, `Forbidden` when re-authorization is required,
        else the store's error category.
        """
        started = time.monotonic()
        token = self._store.get(self._namespace, self._key)
        if not token.ok:
            self._log_failed(_ACCESS_TOKEN, str(token.category), started)
            return fail(f"Gmail access token is not available ({token.category}).", token.category)
        if not token.value:
            self._log_failed(_ACCESS_TOKEN, "NotFound", started)
            return fail("Gmail access token is empty.", "NotFound")
        self._logger.debug("gmail access token ready", fields=self._fields(started), operation=_ACCESS_TOKEN)
        return ok(SecretString(token.value))

    def __repr__(self) -> str:
        return f"GmailOauth(namespace={self._namespace!r}, key={self._key!r})"

    def _fields(self, started: float) -> dict[str, object]:
        return {"namespace": self._namespace, "key": self._key, "elapsed_ms": _elapsed_ms(started)}

    def _log_failed(self, operation: str, category: str, started: float) -> None:
        fields = {**self._fields(started), "category": category}
        self._logger.error("gmail oauth failed", fields=fields, operation=operation)


def _utc_now() -> datetime:
    return datetime.now(UTC)


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
