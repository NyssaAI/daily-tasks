# Responsibility: Prove the Gmail sign-in command seals a read-only grant and reports failures without tokens.
# Public interface:
# (none)
"""`python -m daily_tasks.auth.gmail` behavior with a fake browser, fake token endpoint and in-memory keyring."""

import io
import json
import urllib.parse
import urllib.request
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from nyssa_ai_configuration import BootstrapOptions, KeyringInMemory
from nyssa_ai_result import Ok, Result, ok

from daily_tasks.adapters.communication.gmail_oauth import GmailOauth
from daily_tasks.adapters.communication.gmail_readonly_scope import GMAIL_READONLY_SCOPE
from daily_tasks.auth.gmail import APPLICATION_NAME, main
from daily_tasks.domain import SecretString

ACCESS = "ya29.cli-access-token"
REFRESH = "1//cli-refresh-token"
ENV = {"GMAIL_CLIENT_ID": "cli-client.apps.googleusercontent.com", "GMAIL_CLIENT_SECRET": "gocspx-cli-secret"}


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
class _ConsentingBrowser:
    def open_url(self, url: str) -> Result[None]:
        query = dict(urllib.parse.parse_qsl(urllib.parse.urlsplit(url).query))
        callback = f"{query['redirect_uri']}?{urllib.parse.urlencode({'code': 'c1', 'state': query['state']})}"
        with urllib.request.urlopen(callback, timeout=5) as response:
            response.read()
        return ok(None)


def _google(url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]:
    payload = {"access_token": ACCESS, "refresh_token": REFRESH, "expires_in": 3600, "scope": GMAIL_READONLY_SCOPE}
    return ok((200, json.dumps(payload)))


def _argv(root: Path) -> list[str]:
    return ["--config-dir", str(root / "config"), "--manifest", str(root / "manifest.json")]


def test_gmail_cli_sign_in_seals_grant_and_returns_zero(tmp_path: Path) -> None:
    keyring = KeyringInMemory()
    out = io.StringIO()
    logger = _RecordingLogger()

    code = main(_argv(tmp_path), ENV, keyring, _google, _ConsentingBrowser(), logger, out)

    assert code == 0
    assert "authorized" in out.getvalue()
    disk = "\n".join(p.read_text(encoding="utf-8", errors="replace") for p in tmp_path.rglob("*") if p.is_file())
    assert ACCESS not in disk and REFRESH not in disk and ENV["GMAIL_CLIENT_SECRET"] not in disk
    assert ACCESS not in out.getvalue() + repr(logger.records)
    reopened = GmailOauth.create(
        BootstrapOptions(
            application_name=APPLICATION_NAME,
            configuration_directory=str(tmp_path / "config"),
            manifest_path=str(tmp_path / "manifest.json"),
        ),
        SecretString(ENV["GMAIL_CLIENT_ID"]),
        None,
        logger,
        keyring=keyring,
    )
    assert isinstance(reopened, Ok)
    token = reopened.value.access_token()
    assert isinstance(token, Ok)
    assert token.value.reveal() == ACCESS


def test_gmail_cli_missing_client_id_returns_one(tmp_path: Path) -> None:
    out = io.StringIO()

    code = main(_argv(tmp_path), {}, KeyringInMemory(), _google, _ConsentingBrowser(), _RecordingLogger(), out)

    assert code == 1
    assert "GMAIL_CLIENT_ID" in out.getvalue()


def test_gmail_cli_wider_granted_scope_returns_one(tmp_path: Path) -> None:
    def wide(url: str, form_data: Mapping[str, str]) -> Result[tuple[int, str]]:
        scope = f"{GMAIL_READONLY_SCOPE} https://mail.google.com/"
        return ok((200, json.dumps({"access_token": ACCESS, "refresh_token": REFRESH, "scope": scope})))

    out = io.StringIO()

    code = main(_argv(tmp_path), ENV, KeyringInMemory(), wide, _ConsentingBrowser(), _RecordingLogger(), out)

    assert code == 1
    assert "sign-in failed" in out.getvalue()
    assert ACCESS not in out.getvalue()
