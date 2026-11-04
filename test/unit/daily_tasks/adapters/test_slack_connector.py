# Responsibility: Prove SlackConnector fetches Slack history read-only and advances only the Slack cursor.
# Public interface:
# (none)
"""Slack connector behavior against a fake Slack Web API transport."""

import asyncio
import json
import urllib.parse
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta

from nyssa_ai_result import Err, Ok, Result, fail, ok

from daily_tasks.adapters.communication.slack_channel import SlackChannel
from daily_tasks.adapters.communication.slack_connector import SlackConnector
from daily_tasks.adapters.communication.slack_timestamp import slack_timestamp, slack_ts_from_datetime
from daily_tasks.domain import FetchCursor, FetchCursors, SecretString

TOKEN = "xoxb-secret-token-42"
NOW = datetime(2026, 11, 3, 14, 0, tzinfo=UTC)
SINCE = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)
DEV = SlackChannel(id="C01DEV", name="#dev-core")


@dataclass
class _RecordingLogger:
    records: list[tuple[str, str, Mapping[str, object]]] = field(default_factory=list)

    def debug(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("debug", message, fields or {}))

    def info(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("info", message, fields or {}))

    def warn(self, message: str, fields: Mapping[str, object] | None = None, operation: str = "") -> None:
        self.records.append(("warn", message, fields or {}))

    def error(
        self,
        message: str,
        error: BaseException | None = None,
        fields: Mapping[str, object] | None = None,
        operation: str = "",
    ) -> None:
        self.records.append(("error", message, fields or {}))


@dataclass
class _FakeSlack:
    """Serves `conversations.history` pages per (channel, cursor) and records the requests."""

    pages: dict[tuple[str, str | None], object]
    requests: list[tuple[str, Mapping[str, str]]] = field(default_factory=list)

    def get(self, url: str, headers: Mapping[str, str], timeout_seconds: float) -> Result[bytes]:
        self.requests.append((url, headers))
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        page = self.pages.get((query["channel"], query.get("cursor")))
        if page is None:
            return fail("http_404", "Unavailable")
        return ok(json.dumps(page).encode())

    def query(self, index: int) -> dict[str, str]:
        return dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(self.requests[index][0]).query))


def _ts(moment: datetime) -> str:
    return slack_ts_from_datetime(moment)


def _raw(moment: datetime, text: str, user: str = "U01SARAH") -> dict[str, object]:
    return {"type": "message", "ts": _ts(moment), "user": user, "text": text, "user_profile": {"real_name": "Sarah"}}


def _connector(
    http: _FakeSlack, logger: _RecordingLogger, channels: tuple[SlackChannel, ...] = (DEV,)
) -> SlackConnector:
    return SlackConnector(SecretString(TOKEN), channels, logger, clock=lambda: NOW, http=http, workspace_domain="acme")


def _cursors(slack: FetchCursor | None) -> FetchCursors:
    gmail = FetchCursor(since=SINCE, last_external_id="g1", last_run_at=SINCE, last_status="ok", last_error=None)
    cursors = {"gmail": gmail} | ({"slack": slack} if slack is not None else {})
    return FetchCursors(workspace_root="/vault", cursors=cursors)


def test_slack_connector_incremental_fetch_maps_messages_and_advances_only_slack_cursor() -> None:
    first, second = SINCE + timedelta(minutes=5), SINCE + timedelta(minutes=9)
    http = _FakeSlack({("C01DEV", None): {"ok": True, "messages": [_raw(second, "PR merged"), _raw(first, "Hi")]}})
    since = _cursors(
        FetchCursor(since=SINCE, last_external_id=None, last_run_at=None, last_status="ok", last_error=None)
    )

    result = asyncio.run(_connector(http, _RecordingLogger()).fetch_new_messages(since))

    assert isinstance(result, Ok)
    assert [m.body for m in result.value.messages] == ["Hi", "PR merged"]
    message = result.value.messages[1]
    assert message.id == f"slack:C01DEV:{_ts(second)}"
    assert message.source == "slack"
    assert message.channel == "#dev-core"
    assert message.received_at == second
    assert (message.sender.name, message.sender.address) == ("Sarah", "U01SARAH")
    assert message.url == f"https://acme.slack.com/archives/C01DEV/p{_ts(second).replace('.', '')}"
    assert http.query(0)["oldest"] == _ts(SINCE)
    slack = result.value.cursors.cursors["slack"]
    assert (slack.since, slack.last_external_id, slack.last_status) == (second, f"C01DEV:{_ts(second)}", "ok")
    assert result.value.cursors.cursors["gmail"] == since.cursors["gmail"]


def test_slack_connector_message_at_cursor_is_not_returned_again() -> None:
    seen, same_second_other = SINCE, SINCE
    http = _FakeSlack(
        {
            ("C01DEV", None): {"ok": True, "messages": [_raw(seen, "already fetched")]},
            ("D01IM", None): {"ok": True, "messages": [_raw(same_second_other, "new dm")]},
        }
    )
    cursor = FetchCursor(
        since=SINCE, last_external_id=f"C01DEV:{_ts(seen)}", last_run_at=SINCE, last_status="ok", last_error=None
    )
    channels = (DEV, SlackChannel(id="D01IM", name="dm:sarah"))

    result = asyncio.run(_connector(http, _RecordingLogger(), channels).fetch_new_messages(_cursors(cursor)))

    assert isinstance(result, Ok)
    assert [m.body for m in result.value.messages] == ["new dm"]


def test_slack_connector_follows_pagination_and_skips_channel_noise() -> None:
    http = _FakeSlack(
        {
            ("C01DEV", None): {
                "ok": True,
                "messages": [_raw(SINCE + timedelta(minutes=2), "page one")],
                "has_more": True,
                "response_metadata": {"next_cursor": "bmV4dA=="},
            },
            ("C01DEV", "bmV4dA=="): {
                "ok": True,
                "messages": [{**_raw(SINCE + timedelta(minutes=1), "joined"), "subtype": "channel_join"}],
            },
        }
    )

    result = asyncio.run(_connector(http, _RecordingLogger()).fetch_new_messages(_cursors(None)))

    assert isinstance(result, Ok)
    assert [m.body for m in result.value.messages] == ["page one"]
    assert len(http.requests) == 2


def test_slack_connector_without_cursor_starts_from_7_day_initial_lookback() -> None:
    http = _FakeSlack({("C01DEV", None): {"ok": True, "messages": []}})

    result = asyncio.run(_connector(http, _RecordingLogger()).fetch_new_messages(_cursors(None)))

    assert isinstance(result, Ok)
    assert http.query(0)["oldest"] == _ts(NOW - timedelta(days=7))
    slack = result.value.cursors.cursors["slack"]
    assert (slack.since, slack.last_external_id, slack.last_run_at) == (NOW - timedelta(days=7), None, NOW)


def test_slack_connector_api_error_fails_with_code_and_never_leaks_token() -> None:
    http = _FakeSlack({("C01DEV", None): {"ok": False, "error": "token_revoked"}})
    logger = _RecordingLogger()

    result = asyncio.run(_connector(http, logger).fetch_new_messages(_cursors(None)))

    assert isinstance(result, Err)
    assert result.message == "token_revoked"
    assert str(result.category) == "Forbidden"
    assert logger.records[-1][0] == "error"
    assert logger.records[-1][2]["error"] == "token_revoked"
    assert TOKEN not in repr(logger.records)
    assert http.requests[0][1]["Authorization"] == f"Bearer {TOKEN}"


def test_slack_connector_invalid_json_fails_with_validation() -> None:
    http = _FakeSlack({("C01DEV", None): {"ok": True, "messages": [{"ts": "not-a-ts"}]}})

    result = asyncio.run(_connector(http, _RecordingLogger()).fetch_new_messages(_cursors(None)))

    assert isinstance(result, Err)
    assert (result.message, str(result.category)) == ("invalid_response", "Validation")


def test_slack_connector_timestamp_round_trip_keeps_microseconds() -> None:
    moment = datetime(2024, 11, 3, 13, 20, 0, 100, tzinfo=UTC)

    assert slack_ts_from_datetime(moment) == "1730640000.000100"
    assert slack_timestamp("1730640000.000100") == moment
