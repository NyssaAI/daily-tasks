# Responsibility: Fetch new Slack messages read-only from configured conversations and advance the Slack cursor.
# Public interface:
# `-- SlackConnector
#     +-- SOURCE
#     +-- fetch_new_messages(since)
#     +-- name
#     `-- new(token, channels, logger, clock, http, workspace_domain, initial_lookback, page_size, timeout_seconds)
"""Read-only Slack `CommunicationPort` over `conversations.history` (scopes `channels:history`, `im:history`)."""

import asyncio
import json
import time
import urllib.parse
from collections.abc import Callable, Sequence
from datetime import datetime, timedelta
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.adapters.communication.slack_channel import SlackChannel
from daily_tasks.adapters.communication.slack_history_page import SlackHistoryPage
from daily_tasks.adapters.communication.slack_http import SlackHttp
from daily_tasks.adapters.communication.slack_http_urllib import SlackHttpUrllib
from daily_tasks.adapters.communication.slack_message import slack_message
from daily_tasks.adapters.communication.slack_raw_message import SlackRawMessage
from daily_tasks.adapters.communication.slack_timestamp import slack_ts_from_datetime
from daily_tasks.domain import FetchCursor, FetchCursors, Message, SecretString
from daily_tasks.ports import FetchBatch, PortLogger

_OPERATION: Final = "slack.fetch_new_messages"
_API_BASE: Final = "https://slack.com/api"
_PAGE: Final[TypeAdapter[SlackHistoryPage]] = TypeAdapter(SlackHistoryPage)
_NOISE_SUBTYPES: Final = frozenset(
    {"channel_join", "channel_leave", "channel_topic", "channel_purpose", "channel_name", "channel_archive"}
)
_FORBIDDEN_ERRORS: Final = frozenset(
    {
        "not_authed",
        "invalid_auth",
        "token_revoked",
        "token_expired",
        "account_inactive",
        "missing_scope",
        "not_in_channel",
    }
)


@final
class SlackConnector:
    """Read Slack history newer than the `slack` cursor; it never posts, edits or marks messages read.

    Messages exactly at the cursor timestamp are requested again (`inclusive`) so a same-second message
    in another conversation is not lost; the one recorded in `last_external_id` is dropped.
    """

    SOURCE: ClassVar[str] = "slack"

    def __init__(
        self,
        token: SecretString,
        channels: Sequence[SlackChannel],
        logger: PortLogger,
        clock: Callable[[], datetime],
        http: SlackHttp | None = None,
        workspace_domain: str | None = None,
        initial_lookback: timedelta = timedelta(days=1),
        page_size: int = 200,
        timeout_seconds: float = 10.0,
    ) -> None:
        """Borrow `token` (resolve it with `slack_token`); `clock` returns aware UTC datetimes.

        `initial_lookback` bounds the first fetch when no `slack` cursor exists. `http=None` uses the
        standard-library transport.
        """
        if page_size < 1:
            raise ValueError("page_size must be positive")
        self._token = token
        self._channels = tuple(channels)
        self._logger = logger
        self._clock = clock
        self._http: SlackHttp = http if http is not None else SlackHttpUrllib()
        self._workspace_domain = workspace_domain
        self._initial_lookback = initial_lookback
        self._page_size = page_size
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        """Cursor key and `Message.source`: `slack`."""
        return self.SOURCE

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Return messages newer than the `slack` cursor, oldest first, with only that cursor advanced.

        Fails with `Forbidden` for auth/scope errors (`token_revoked`, `missing_scope`, ...), `NotFound`
        for `channel_not_found`, `Unavailable` for transport or other Slack errors and `Validation` for
        an unreadable response; the message is the Slack error code.
        """
        started = time.monotonic()
        previous = since.cursors.get(self.SOURCE)
        fetched_at = self._clock()
        oldest = previous.since if previous is not None else fetched_at - self._initial_lookback
        skip_id = previous.last_external_id if previous is not None else None
        messages: list[Message] = []
        for channel in self._channels:
            history = await self._history(channel, oldest)
            if not history.ok:
                fields = {
                    "channel": channel.id,
                    "error": history.message,
                    "category": str(history.category),
                    "elapsed_ms": _elapsed_ms(started),
                }
                self._logger.error("slack fetch failed", fields=fields, operation=_OPERATION)
                return fail(history.message, history.category)
            for raw in history.value:
                message = slack_message(raw, channel, self._workspace_domain, fetched_at)
                if message.received_at >= oldest and message.external_id != skip_id:
                    messages.append(message)
        messages.sort(key=lambda m: (m.received_at, m.external_id))
        cursor = _advanced(previous, oldest, messages, fetched_at)
        fields = {"channels": len(self._channels), "fetched": len(messages), "elapsed_ms": _elapsed_ms(started)}
        self._logger.info("slack fetch completed", fields=fields, operation=_OPERATION)
        cursors = FetchCursors(workspace_root=since.workspace_root, cursors={**since.cursors, self.SOURCE: cursor})
        return ok(FetchBatch(messages=tuple(messages), cursors=cursors))

    async def _history(self, channel: SlackChannel, oldest: datetime) -> Result[tuple[SlackRawMessage, ...]]:
        collected: list[SlackRawMessage] = []
        page_cursor: str | None = None
        while True:
            query = {
                "channel": channel.id,
                "oldest": slack_ts_from_datetime(oldest),
                "inclusive": "true",
                "limit": str(self._page_size),
            }
            if page_cursor is not None:
                query["cursor"] = page_cursor
            page = await self._page(f"{_API_BASE}/conversations.history?{urllib.parse.urlencode(query)}")
            if not page.ok:
                return page
            collected.extend(m for m in page.value.messages if m.subtype not in _NOISE_SUBTYPES)
            page_cursor = page.value.next_cursor
            if page_cursor is None:
                return ok(tuple(collected))

    async def _page(self, url: str) -> Result[SlackHistoryPage]:
        headers = {"Authorization": f"Bearer {self._token.reveal()}", "Accept": "application/json"}
        body = await asyncio.to_thread(self._http.get, url, headers, self._timeout_seconds)
        if not body.ok:
            return fail(body.message, "Unavailable")
        try:
            page = _PAGE.validate_python(json.loads(body.value))
        except (ValueError, ValidationError) as exc:
            return fail("invalid_response", "Validation", cause=exc)
        if not page.ok:
            code = page.error or "unknown_error"
            return fail(code, _category(code))
        return ok(page)


def _advanced(
    previous: FetchCursor | None, oldest: datetime, messages: Sequence[Message], run_at: datetime
) -> FetchCursor:
    if messages:
        newest = messages[-1]
        return FetchCursor(
            since=newest.received_at,
            last_external_id=newest.external_id,
            last_run_at=run_at,
            last_status="ok",
            last_error=None,
        )
    return FetchCursor(
        since=oldest,
        last_external_id=previous.last_external_id if previous is not None else None,
        last_run_at=run_at,
        last_status="ok",
        last_error=None,
    )


def _category(code: str) -> str:
    if code in _FORBIDDEN_ERRORS:
        return "Forbidden"
    if code == "channel_not_found":
        return "NotFound"
    return "Unavailable"


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
