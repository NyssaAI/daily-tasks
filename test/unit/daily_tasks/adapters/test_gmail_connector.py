"""Responsibility: Prove GmailConnector fetches Gmail read-only, maps messages and advances only the Gmail cursor.
Public interface:
+-- LIST_URL
+-- NOW
+-- SINCE
+-- TOKEN
+-- test_gmail_connector_html_only_body_maps_html_format()
+-- test_gmail_connector_incremental_fetch_advances_watermark_without_duplicates()
+-- test_gmail_connector_maps_headers_and_body_to_message()
+-- test_gmail_connector_message_at_last_external_id_is_not_returned_again()
+-- test_gmail_connector_missing_grant_fails_forbidden_without_http_call()
+-- test_gmail_connector_queries_after_cursor_with_bearer_token()
+-- test_gmail_connector_rejected_token_fails_forbidden_and_logs_without_secret(log_capture)
+-- test_gmail_connector_success_logs_counts_and_never_bodies(log_capture)
+-- test_gmail_connector_transport_failure_fails_unavailable()
+-- test_gmail_connector_truncated_fetch_logs_warning(log_capture)
`-- test_gmail_connector_without_cursor_starts_from_7_day_lookback_and_creates_cursor()

Gmail connector behavior against a fake Gmail REST v1 transport and a fake token source.
"""

import asyncio
import base64
import json
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime

from nyssa_ai_result import Err, Ok, Result, fail, ok

from conftest import LogCapture
from daily_tasks.adapters.communication.gmail_connector import GmailConnector
from daily_tasks.domain import FetchCursor, FetchCursors, MessageAddress, SecretString

TOKEN = "ya29.gmail-access-token"
NOW = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)
SINCE = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
LIST_URL = "https://gmail.googleapis.com/gmail/v1/users/me/messages"


@dataclass
class _TokenSource:
    token: Result[SecretString] = field(default_factory=lambda: ok(SecretString(TOKEN)))

    def access_token(self) -> Result[SecretString]:
        return self.token


@dataclass
class _FakeGmail:
    """Serves messages newer than the `after:` query; records every request."""

    messages: dict[str, dict[str, object]]
    status: str | None = None
    requests: list[tuple[str, Mapping[str, str]]] = field(default_factory=list)

    def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]:
        self.requests.append((url, headers))
        if self.status is not None:
            return fail(self.status, "Unavailable")
        parts = urllib.parse.urlsplit(url)
        query = dict(urllib.parse.parse_qsl(parts.query))
        if parts.path.endswith("/messages"):
            after_ms = int(query["q"].removeprefix("after:")) * 1000
            refs = [
                {"id": mid, "threadId": str(m["threadId"])}
                for mid, m in self.messages.items()
                if int(str(m["internalDate"])) >= after_ms
            ]
            return ok(json.dumps({"messages": refs} if refs else {"resultSizeEstimate": 0}).encode())
        message = self.messages.get(parts.path.rsplit("/", 1)[-1])
        return ok(json.dumps(message).encode()) if message is not None else fail("http_404", "Unavailable")


def _b64(text: str) -> str:
    return base64.urlsafe_b64encode(text.encode()).decode().rstrip("=")


def _raw(
    mid: str, moment: datetime, subject: str = "Re: Gmail connector", body: str = "Hi Jordan"
) -> dict[str, object]:
    return {
        "id": mid,
        "threadId": f"t-{mid}",
        "internalDate": str(int(moment.timestamp() * 1000)),
        "snippet": body[:40],
        "labelIds": ["INBOX"],
        "payload": {
            "mimeType": "multipart/alternative",
            "headers": [
                {"name": "From", "value": "Sarah Chen <sarah@example.com>"},
                {"name": "To", "value": "Jordan <jordan@example.com>, ops@example.com"},
                {"name": "Cc", "value": "Alex <alex@example.com>"},
                {"name": "Subject", "value": "Re: Gmail connector"},
            ],
            "parts": [
                {"mimeType": "text/html", "body": {"size": 10, "data": _b64(f"<p>{body}</p>")}},
                {"mimeType": "text/plain", "body": {"size": 10, "data": _b64(body)}},
                {"mimeType": "image/png", "filename": "shot.png", "body": {"size": 99, "attachmentId": "a1"}},
            ],
        },
    }


def _cursors(cursor: FetchCursor | None = None) -> FetchCursors:
    slack = FetchCursor(since=SINCE, last_external_id="C1:1.0", last_run_at=None, last_status="error", last_error="x")
    cursors = {"slack": slack} if cursor is None else {"slack": slack, "gmail": cursor}
    return FetchCursors(workspace_root="/vault", cursors=cursors)


def _cursor(since: datetime, last_id: str | None = None) -> FetchCursor:
    return FetchCursor(since=since, last_external_id=last_id, last_run_at=None, last_status="ok", last_error=None)


def _connector(http: _FakeGmail, tokens: _TokenSource | None = None) -> GmailConnector:
    return GmailConnector(tokens or _TokenSource(), clock=lambda: NOW, http=http)


def test_gmail_connector_maps_headers_and_body_to_message() -> None:
    received = datetime(2026, 11, 3, 12, 41, 9, tzinfo=UTC)
    http = _FakeGmail({"18f2": _raw("18f2", received)})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Ok)
    (message,) = result.value.messages
    assert message.id == "gmail:18f2"
    assert (message.source, message.external_id, message.channel) == ("gmail", "18f2", "email")
    assert message.thread_id == "gmail-thread:t-18f2"
    assert message.received_at == received
    assert message.sender == MessageAddress(name="Sarah Chen", address="sarah@example.com")
    assert message.to == (
        MessageAddress(name="Jordan", address="jordan@example.com"),
        MessageAddress(name=None, address="ops@example.com"),
    )
    assert message.cc == (MessageAddress(name="Alex", address="alex@example.com"),)
    assert message.subject == "Re: Gmail connector"
    assert (message.body, message.body_format, message.snippet) == ("Hi Jordan", "text", "Hi Jordan")
    assert message.url == "https://mail.google.com/mail/u/0/#all/t-18f2"
    assert message.fetched_at == NOW


def test_gmail_connector_html_only_body_maps_html_format() -> None:
    raw = _raw("h1", datetime(2026, 11, 3, 13, tzinfo=UTC), body="Status")
    payload = raw["payload"]
    assert isinstance(payload, dict)
    payload["parts"] = [payload["parts"][0]]
    http = _FakeGmail({"h1": raw})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Ok)
    assert (result.value.messages[0].body, result.value.messages[0].body_format) == ("<p>Status</p>", "html")


def test_gmail_connector_queries_after_cursor_with_bearer_token() -> None:
    http = _FakeGmail({})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Ok)
    url, headers = http.requests[0]
    assert url.startswith(LIST_URL + "?")
    assert dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))["q"] == f"after:{int(SINCE.timestamp())}"
    assert headers["Authorization"] == f"Bearer {TOKEN}"


def test_gmail_connector_incremental_fetch_advances_watermark_without_duplicates() -> None:
    first_at = datetime(2026, 11, 3, 12, 30, tzinfo=UTC)
    second_at = datetime(2026, 11, 3, 13, 15, tzinfo=UTC)
    http = _FakeGmail({"m1": _raw("m1", first_at)})
    connector = _connector(http)

    first = asyncio.run(connector.fetch_new_messages(_cursors(_cursor(SINCE))))
    assert isinstance(first, Ok)
    http.messages["m2"] = _raw("m2", second_at)
    second = asyncio.run(connector.fetch_new_messages(first.value.cursors))
    assert isinstance(second, Ok)
    third = asyncio.run(connector.fetch_new_messages(second.value.cursors))
    assert isinstance(third, Ok)

    assert [m.external_id for m in first.value.messages] == ["m1"]
    assert [m.external_id for m in second.value.messages] == ["m2"]
    assert third.value.messages == ()
    gmail = third.value.cursors.cursors["gmail"]
    assert (gmail.since, gmail.last_external_id, gmail.last_status, gmail.last_run_at) == (second_at, "m2", "ok", NOW)
    assert third.value.cursors.cursors["slack"] == _cursors().cursors["slack"]


def test_gmail_connector_message_at_last_external_id_is_not_returned_again() -> None:
    at = datetime(2026, 11, 3, 12, 30, tzinfo=UTC)
    http = _FakeGmail({"m1": _raw("m1", at), "m0": _raw("m0", SINCE)})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE, "m0"))))

    assert isinstance(result, Ok)
    assert [m.external_id for m in result.value.messages] == ["m1"]


def test_gmail_connector_without_cursor_starts_from_7_day_lookback_and_creates_cursor() -> None:
    http = _FakeGmail({})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors()))

    assert isinstance(result, Ok)
    gmail = result.value.cursors.cursors["gmail"]
    assert gmail.since == datetime(2026, 10, 27, 14, 0, tzinfo=UTC)
    assert gmail.last_external_id is None


def test_gmail_connector_rejected_token_fails_forbidden_and_logs_without_secret(log_capture: LogCapture) -> None:
    http = _FakeGmail({}, status="http_401")

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Err)
    assert result.category == "Forbidden"
    assert log_capture.records[-1][0:2] == ("error", "gmail fetch failed")
    assert TOKEN not in repr(log_capture.records)


def test_gmail_connector_missing_grant_fails_forbidden_without_http_call() -> None:
    http = _FakeGmail({})
    tokens = _TokenSource(fail("Gmail access token is not available.", "NotFound"))

    result = asyncio.run(_connector(http, tokens).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Err)
    assert result.category == "Forbidden"
    assert http.requests == []


def test_gmail_connector_transport_failure_fails_unavailable() -> None:
    http = _FakeGmail({}, status="network_error")

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Err)
    assert result.category == "Unavailable"


def test_gmail_connector_success_logs_counts_and_never_bodies(log_capture: LogCapture) -> None:
    http = _FakeGmail({"m1": _raw("m1", datetime(2026, 11, 3, 12, 30, tzinfo=UTC), body="confidential plan")})

    result = asyncio.run(_connector(http).fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Ok)
    level, message, fields = log_capture.records[-1]
    assert (level, message, fields["fetched"]) == ("info", "gmail fetch completed", 1)
    assert "confidential" not in repr(log_capture.records)
    assert TOKEN not in repr(log_capture.records)


def test_gmail_connector_truncated_fetch_logs_warning(log_capture: LogCapture) -> None:
    http = _FakeGmail({f"m{i}": _raw(f"m{i}", datetime(2026, 11, 3, 13, i, tzinfo=UTC)) for i in range(3)})
    connector = GmailConnector(_TokenSource(), clock=lambda: NOW, http=http, max_messages=2)

    result = asyncio.run(connector.fetch_new_messages(_cursors(_cursor(SINCE))))

    assert isinstance(result, Ok)
    assert len(result.value.messages) == 2
    assert ("warn", "gmail fetch truncated") in [(level, message) for level, message, _ in log_capture.records]
