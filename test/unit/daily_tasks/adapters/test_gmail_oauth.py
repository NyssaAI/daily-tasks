# Responsibility: Prove GmailOauth signs in read-only, stores the grant sealed and refreshes it headlessly.
# Public interface:
# (none)
"""Gmail OAuth against a fake Google token endpoint, a fake browser and an in-memory keyring."""

import json
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from pathlib import Path

from nyssa_ai_configuration import BootstrapOptions, KeyringInMemory
from nyssa_ai_result import Err, Ok, Result, fail, ok

from daily_tasks.adapters.communication.gmail_oauth import GmailOauth
from daily_tasks.adapters.communication.gmail_readonly_scope import GMAIL_READONLY_SCOPE, GOOGLE_TOKEN_ENDPOINT
from daily_tasks.domain import SecretString

APP = "daily-tasks-test"
CLIENT_ID = "client-123.apps.googleusercontent.com"
CLIENT_SECRET = "gocspx-client-secret-xyz"
ACCESS_1 = "ya29.first-access-token"
ACCESS_2 = "ya29.second-access-token"
REFRESH = "1//refresh-token-abc"
SECRETS = (CLIENT_SECRET, ACCESS_1, ACCESS_2, REFRESH)


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
class _Clock:
    now: datetime = datetime(2026, 11, 3, 12, 0, tzinfo=UTC)

    def __call__(self) -> datetime:
        return self.now


@dataclass
class _FakeGoogle:
    """Token endpoint: answers queued (status, payload) responses and records the posted forms."""

    responses: list[tuple[int, dict[str, object]]]
    forms: list[tuple[str, dict[str, str]]] = field(default_factory=list)

    def post(self, url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]:
        self.forms.append((url, dict(form_data)))
        if not self.responses:
            return fail("unexpected token request", "Unavailable")
        status, payload = self.responses.pop(0)
        return ok((status, json.dumps(payload)))


@dataclass
class _ConsentingBrowser:
    """Plays the user approving consent: calls the loopback redirect with a code and the sent state."""

    urls: list[str] = field(default_factory=list)

    def open_url(self, url: str) -> Result[None]:
        self.urls.append(url)
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        callback = f"{query['redirect_uri']}?{urllib.parse.urlencode({'code': 'auth-code-1', 'state': query['state']})}"
        with urllib.request.urlopen(callback, timeout=5) as response:
            response.read()
        return ok(None)


def _token(access: str, scope: str = GMAIL_READONLY_SCOPE, expires_in: int = 3600) -> dict[str, object]:
    return {"access_token": access, "refresh_token": REFRESH, "expires_in": expires_in, "scope": scope}


def _options(root: Path) -> BootstrapOptions:
    return BootstrapOptions(
        application_name=APP, configuration_directory=str(root / "config"), manifest_path=str(root / "manifest.json")
    )


def _oauth(
    root: Path, keyring: KeyringInMemory, google: _FakeGoogle, clock: _Clock, logger: _RecordingLogger
) -> GmailOauth:
    created = GmailOauth.create(
        _options(root),
        SecretString(CLIENT_ID),
        SecretString(CLIENT_SECRET),
        logger,
        keyring=keyring,
        http_post=google.post,
        now=clock,
        browser_launcher=_ConsentingBrowser(),
    )
    assert isinstance(created, Ok)
    return created.value


def _disk_text(root: Path) -> str:
    return "\n".join(path.read_text(encoding="utf-8", errors="replace") for path in root.rglob("*") if path.is_file())


def test_gmail_oauth_authorize_exchanges_code_and_stores_grant_sealed(tmp_path: Path) -> None:
    google = _FakeGoogle([(200, _token(ACCESS_1))])
    logger = _RecordingLogger()
    oauth = _oauth(tmp_path, KeyringInMemory(), google, _Clock(), logger)

    authorized = oauth.authorize()
    token = oauth.access_token()

    assert isinstance(authorized, Ok)
    assert isinstance(token, Ok)
    assert token.value.reveal() == ACCESS_1
    url, form = google.forms[0]
    assert url == GOOGLE_TOKEN_ENDPOINT
    assert form["grant_type"] == "authorization_code"
    assert form["code"] == "auth-code-1"
    assert form["client_secret"] == CLIENT_SECRET
    assert form["code_verifier"]
    assert all(secret not in _disk_text(tmp_path) for secret in SECRETS)


def test_gmail_oauth_authorize_requests_only_readonly_scope(tmp_path: Path) -> None:
    browser = _ConsentingBrowser()
    google = _FakeGoogle([(200, _token(ACCESS_1))])
    created = GmailOauth.create(
        _options(tmp_path),
        SecretString(CLIENT_ID),
        None,
        _RecordingLogger(),
        keyring=KeyringInMemory(),
        http_post=google.post,
        browser_launcher=browser,
    )
    assert isinstance(created, Ok)

    assert isinstance(created.value.authorize(), Ok)

    query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(browser.urls[0]).query))
    assert browser.urls[0].startswith("https://accounts.google.com/o/oauth2/v2/auth?")
    assert query["scope"] == GMAIL_READONLY_SCOPE
    assert query["code_challenge_method"] == "S256"
    assert "client_secret" not in google.forms[0][1]


def test_gmail_oauth_authorize_extra_scope_fails_validation_without_browser(tmp_path: Path) -> None:
    google = _FakeGoogle([(200, _token(ACCESS_1))])
    logger = _RecordingLogger()
    oauth = _oauth(tmp_path, KeyringInMemory(), google, _Clock(), logger)

    result = oauth.authorize((GMAIL_READONLY_SCOPE, "https://www.googleapis.com/auth/gmail.send"))

    assert isinstance(result, Err)
    assert result.category == "Validation"
    assert google.forms == []
    assert logger.records[-1][0] == "error"


def test_gmail_oauth_granted_wider_scope_fails_forbidden_and_stores_nothing(tmp_path: Path) -> None:
    wide = f"{GMAIL_READONLY_SCOPE} https://www.googleapis.com/auth/gmail.modify"
    google = _FakeGoogle([(200, _token(ACCESS_1, scope=wide))])
    oauth = _oauth(tmp_path, KeyringInMemory(), google, _Clock(), _RecordingLogger())

    authorized = oauth.authorize()
    token = oauth.access_token()

    assert isinstance(authorized, Err)
    assert authorized.category == "Forbidden"
    assert isinstance(token, Err)
    assert token.category == "NotFound"


def test_gmail_oauth_expiring_token_refreshes_without_browser(tmp_path: Path) -> None:
    clock = _Clock()
    google = _FakeGoogle([(200, _token(ACCESS_1)), (200, {"access_token": ACCESS_2, "expires_in": 3600})])
    oauth = _oauth(tmp_path, KeyringInMemory(), google, clock, _RecordingLogger())
    assert isinstance(oauth.authorize(), Ok)

    clock.now += timedelta(minutes=56)
    refreshed = oauth.access_token()
    again = oauth.access_token()

    assert isinstance(refreshed, Ok)
    assert refreshed.value.reveal() == ACCESS_2
    assert isinstance(again, Ok)
    assert again.value.reveal() == ACCESS_2
    assert [form["grant_type"] for _, form in google.forms] == ["authorization_code", "refresh_token"]
    assert google.forms[1][1]["refresh_token"] == REFRESH
    assert google.forms[1][1]["client_secret"] == CLIENT_SECRET
    assert all(secret not in _disk_text(tmp_path) for secret in SECRETS)


def test_gmail_oauth_revoked_refresh_token_fails_forbidden(tmp_path: Path) -> None:
    clock = _Clock()
    google = _FakeGoogle([(200, _token(ACCESS_1)), (400, {"error": "invalid_grant"})])
    logger = _RecordingLogger()
    oauth = _oauth(tmp_path, KeyringInMemory(), google, clock, logger)
    assert isinstance(oauth.authorize(), Ok)

    clock.now += timedelta(hours=2)
    result = oauth.access_token()

    assert isinstance(result, Err)
    assert result.category == "Forbidden"
    assert logger.records[-1][0] == "error"
    assert logger.records[-1][2]["category"] == "Forbidden"


def test_gmail_oauth_grant_survives_restart_with_same_keyring(tmp_path: Path) -> None:
    keyring = KeyringInMemory()
    first = _oauth(tmp_path, keyring, _FakeGoogle([(200, _token(ACCESS_1))]), _Clock(), _RecordingLogger())
    assert isinstance(first.authorize(), Ok)

    reopened = _oauth(tmp_path, keyring, _FakeGoogle([]), _Clock(), _RecordingLogger())
    token = reopened.access_token()

    assert isinstance(token, Ok)
    assert token.value.reveal() == ACCESS_1


def test_gmail_oauth_tokens_never_appear_in_repr_or_logs(tmp_path: Path) -> None:
    logger = _RecordingLogger()
    oauth = _oauth(tmp_path, KeyringInMemory(), _FakeGoogle([(200, _token(ACCESS_1))]), _Clock(), logger)
    assert isinstance(oauth.authorize(), Ok)

    token = oauth.access_token()

    assert isinstance(token, Ok)
    rendered = f"{oauth!r} {token!r} {token.value} {logger.records!r}"
    assert all(secret not in rendered for secret in SECRETS)
    assert logger.records[-1][2]["elapsed_ms"] is not None
