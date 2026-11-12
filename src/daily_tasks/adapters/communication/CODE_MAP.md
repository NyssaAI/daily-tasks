# Code Map: `communication`
[Up: adapters](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../../auth/gmail.py`](../../auth/gmail.py) -> `gmail`
* **Caller**: [`../../domain/ports.py`](../../domain/ports.py) -> `ports`
* **Caller**: [`../../domain/__init__.py`](../../domain/__init__.py) -> `__init__`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Group the read-only communication source adapters.
* **Ubiquitous Language Concepts**: [`reject`](../../../../docs/concepts/c-03-explicit-adjudication-and-decision-log.md)

```text
__init__.py
`-- (no public symbols)

communication_multiplexer.py
`-- class CommunicationMultiplexer
    |-- def __init__(self, ports: Sequence[CommunicationPort], clock: Callable[[], datetime]) -> None
    `-- def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]

compute_fetch_window.py
|-- DEFAULT_INITIAL_LOOKBACK_DAYS: Final = 7
`-- def compute_fetch_window( cursors: FetchCursors, source: str, now: datetime, initial_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS ) -> FetchWindow

fetch_window.py
`-- class FetchWindow

gmail_connector.py
`-- class GmailConnector
    |-- def __init__( self, token_source: GmailTokenSource, clock: Callable[[], datetime], http: GmailHttp | None = None, initial_lookback: timedelta = timedelta(days=7), page_size: int = 100, max_messages: int = 500, timeout_seconds: float = 15.0, ) -> None
    `-- def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]

gmail_header.py
`-- class GmailHeader

gmail_http.py
`-- class GmailHttp(Protocol)
    `-- def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]

gmail_http_urllib.py
`-- class GmailHttpUrllib
    `-- def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]

gmail_message.py
`-- def gmail_message(raw: GmailRawMessage, fetched_at: datetime) -> Message

gmail_message_list.py
`-- class GmailMessageList

gmail_message_part.py
`-- class GmailMessagePart

gmail_oauth.py
`-- class GmailOauth
    |-- def __init__( self, store: GmailTokenStore, client_id: SecretString, browser_launcher: BrowserLauncher | None = None, namespace: str = DEFAULT_NAMESPACE, key: str = DEFAULT_KEY, ) -> None
    |-- def authorize( self, scopes: Sequence[str] = (GMAIL_READONLY_SCOPE,), redirect_port: int | None = None, ) -> Result[None]
    `-- def access_token(self) -> Result[SecretString]

gmail_part_body.py
`-- class GmailPartBody

gmail_raw_message.py
`-- class GmailRawMessage

gmail_readonly_scope.py
|-- GMAIL_READONLY_SCOPE: Final
|-- GOOGLE_AUTHORIZATION_ENDPOINT: Final
`-- GOOGLE_TOKEN_ENDPOINT: Final

gmail_token_endpoint.py
`-- class GmailTokenEndpoint
    |-- def __init__(self, client_secret: SecretString | None, http_post: _HttpPost | None = None) -> None
    `-- def post(self, url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]

gmail_token_source.py
`-- class GmailTokenSource(Protocol)
    `-- def access_token(self) -> Result[SecretString]

gmail_token_store.py
`-- class GmailTokenStore(Protocol)
    |-- def authorize( self, namespace: str, key: str, options: OAuthOptions, browser_launcher: BrowserLauncher | None = None ) -> Result[None]
    `-- def get(self, namespace: str, key: str) -> Result[str]

ingest_harness_messages.py
`-- def ingest_harness_messages( messages: Sequence[Message], since: FetchCursors, now: datetime, initial_lookback_days: int = DEFAULT_INITIAL_LOOKBACK_DAYS, checked_sources: Sequence[str] = (), ) -> FetchBatch

slack_channel.py
`-- class SlackChannel

slack_connector.py
`-- class SlackConnector
    |-- def __init__( self, token: SecretString, channels: Sequence[SlackChannel], clock: Callable[[], datetime], http: SlackHttp | None = None, workspace_domain: str | None = None, initial_lookback: timedelta = timedelta(days=7), page_size: int = 200, timeout_seconds: float = 10.0, ) -> None
    `-- def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]

slack_history_page.py
`-- class SlackHistoryPage

slack_http.py
`-- class SlackHttp(Protocol)
    `-- def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]

slack_http_urllib.py
`-- class SlackHttpUrllib
    `-- def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]

slack_message.py
|-- SNIPPET_LENGTH: Final = 200
`-- def slack_message( raw: SlackRawMessage, channel: SlackChannel, workspace_domain: str | None, fetched_at: datetime ) -> Message

slack_raw_message.py
`-- class SlackRawMessage

slack_timestamp.py
|-- def slack_timestamp(value: str) -> datetime
`-- def slack_ts_from_datetime(value: datetime) -> str

slack_token.py
|-- SLACK_TOKEN_ENV_VAR: Final = "SLACK_BOT_TOKEN"
`-- def slack_token( resolver: SecretResolver, namespace: str = "communication", key: str = "slack", env_var: str = SLACK_TOKEN_ENV_VAR ) -> Result[SecretString]
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
