# Responsibility: Fetch new Gmail messages read-only and advance the Gmail cursor.
# Public interface:
# `-- GmailConnector
#     +-- SOURCE
#     +-- fetch_new_messages(since)
#     +-- name
#     `-- new(token_source, logger, clock, http, initial_lookback, page_size, max_messages, timeout_seconds)
"""Read-only Gmail `CommunicationPort` over REST v1 `users.messages.list/get`; zero LLM calls."""

import asyncio
import json
import time
import urllib.parse
from collections.abc import Callable, Mapping, Sequence
from datetime import datetime, timedelta
from typing import ClassVar, Final, final

from nyssa_ai_result import Result, fail, ok
from pydantic import TypeAdapter, ValidationError

from daily_tasks.adapters.communication.gmail_http import GmailHttp
from daily_tasks.adapters.communication.gmail_http_urllib import GmailHttpUrllib
from daily_tasks.adapters.communication.gmail_message import gmail_message
from daily_tasks.adapters.communication.gmail_message_list import GmailMessageList
from daily_tasks.adapters.communication.gmail_raw_message import GmailRawMessage
from daily_tasks.adapters.communication.gmail_token_source import GmailTokenSource
from daily_tasks.domain import FetchCursor, FetchCursors, Message
from daily_tasks.ports import FetchBatch, PortLogger

_OPERATION: Final = "gmail.fetch_new_messages"
_API_BASE: Final = "https://gmail.googleapis.com/gmail/v1/users/me/messages"
_LIST: Final[TypeAdapter[GmailMessageList]] = TypeAdapter(GmailMessageList)
_MESSAGE: Final[TypeAdapter[GmailRawMessage]] = TypeAdapter(GmailRawMessage)


@final
class GmailConnector:
    """Read Gmail messages newer than the `gmail` cursor; it never sends, drafts, labels or marks read.

    Gmail's `after:` filter has one-second resolution, so the cursor second is queried again and
    messages at or before the cursor are dropped, as is the one recorded in `last_external_id`.
    """

    SOURCE: ClassVar[str] = "gmail"

    def __init__(
        self,
        token_source: GmailTokenSource,
        logger: PortLogger,
        clock: Callable[[], datetime],
        http: GmailHttp | None = None,
        initial_lookback: timedelta = timedelta(days=1),
        page_size: int = 100,
        max_messages: int = 500,
        timeout_seconds: float = 15.0,
    ) -> None:
        """Borrow `token_source` (usually `GmailOAuth`); `clock` returns aware UTC datetimes.

        `initial_lookback` bounds the first fetch when no `gmail` cursor exists; `max_messages` bounds
        one fetch (newest first; a truncated fetch logs a warning). `http=None` uses the standard-library transport.
        """
        if page_size < 1 or max_messages < 1:
            raise ValueError("page_size and max_messages must be positive")
        self._token_source = token_source
        self._logger = logger
        self._clock = clock
        self._http: GmailHttp = http if http is not None else GmailHttpUrllib()
        self._initial_lookback = initial_lookback
        self._page_size = page_size
        self._max_messages = max_messages
        self._timeout_seconds = timeout_seconds

    @property
    def name(self) -> str:
        """Cursor key and `Message.source`: `gmail`."""
        return self.SOURCE

    async def fetch_new_messages(self, since: FetchCursors) -> Result[FetchBatch]:
        """Return messages newer than the `gmail` cursor, oldest first, with only that cursor advanced.

        Fails with `Forbidden` when sign-in is required or Google rejects the token (`http_401`,
        `http_403`), `Unavailable` for transport errors and `Validation` for an unreadable response.
        """
        started = time.monotonic()
        previous = since.cursors.get(self.SOURCE)
        fetched_at = self._clock()
        oldest = previous.since if previous is not None else fetched_at - self._initial_lookback
        skip_id = previous.last_external_id if previous is not None else None
        fetched = await self._fetch(oldest, fetched_at)
        if not fetched.ok:
            fields = {"error": fetched.message, "category": str(fetched.category), "elapsed_ms": _elapsed_ms(started)}
            self._logger.error("gmail fetch failed", fields=fields, operation=_OPERATION)
            return fail(fetched.message, fetched.category)
        messages = sorted(
            (m for m in fetched.value if m.external_id != skip_id and _is_new(m, oldest, previous is not None)),
            key=lambda m: (m.received_at, m.external_id),
        )
        if len(fetched.value) >= self._max_messages:
            warn_fields = {"max_messages": self._max_messages, "elapsed_ms": _elapsed_ms(started)}
            self._logger.warn("gmail fetch truncated", fields=warn_fields, operation=_OPERATION)
        cursor = _advanced(previous, oldest, messages, fetched_at)
        fields = {"fetched": len(messages), "listed": len(fetched.value), "elapsed_ms": _elapsed_ms(started)}
        self._logger.info("gmail fetch completed", fields=fields, operation=_OPERATION)
        cursors = FetchCursors(workspace_root=since.workspace_root, cursors={**since.cursors, self.SOURCE: cursor})
        return ok(FetchBatch(messages=tuple(messages), cursors=cursors))

    async def _fetch(self, oldest: datetime, fetched_at: datetime) -> Result[tuple[Message, ...]]:
        token = self._token_source.access_token()
        if not token.ok:
            return fail("gmail_auth_required", "Forbidden")
        headers = {"Authorization": f"Bearer {token.value.reveal()}", "Accept": "application/json"}
        ids = await self._list(int(oldest.timestamp()), headers)
        if not ids.ok:
            return ids
        messages: list[Message] = []
        for message_id in ids.value:
            raw = await self._get(message_id, headers)
            if not raw.ok:
                return raw
            messages.append(gmail_message(raw.value, fetched_at))
        return ok(tuple(messages))

    async def _list(self, after_epoch: int, headers: Mapping[str, str]) -> Result[tuple[str, ...]]:
        ids: list[str] = []
        page_token: str | None = None
        while len(ids) < self._max_messages:
            query = {"q": f"after:{after_epoch}", "maxResults": str(self._page_size)}
            if page_token is not None:
                query["pageToken"] = page_token
            body = await self._call(f"{_API_BASE}?{urllib.parse.urlencode(query)}", headers)
            if not body.ok:
                return body
            try:
                page = _LIST.validate_python(json.loads(body.value))
            except (ValueError, ValidationError) as exc:
                return fail("invalid_response", "Validation", cause=exc)
            ids.extend(ref["id"] for ref in page.messages if ref.get("id"))
            page_token = page.nextPageToken
            if page_token is None:
                break
        return ok(tuple(ids[: self._max_messages]))

    async def _get(self, message_id: str, headers: Mapping[str, str]) -> Result[GmailRawMessage]:
        url = f"{_API_BASE}/{urllib.parse.quote(message_id, safe='')}?format=full"
        body = await self._call(url, headers)
        if not body.ok:
            return body
        try:
            return ok(_MESSAGE.validate_python(json.loads(body.value)))
        except (ValueError, ValidationError) as exc:
            return fail("invalid_response", "Validation", cause=exc)

    async def _call(self, url: str, headers: Mapping[str, str]) -> Result[bytes]:
        body = await asyncio.to_thread(self._http.get, url, headers, self._timeout_seconds)
        if body.ok:
            return body
        category = "Forbidden" if body.message in ("http_401", "http_403") else "Unavailable"
        return fail(body.message, category)


def _is_new(message: Message, oldest: datetime, has_cursor: bool) -> bool:
    return message.received_at > oldest if has_cursor else message.received_at >= oldest


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


def _elapsed_ms(started: float) -> float:
    return round((time.monotonic() - started) * 1000, 3)
