"""Responsibility: Map one Gmail REST message into a canonical CommunicationMessage.
Public interface:
`-- gmail_message(raw, fetched_at)
"""

import base64
import binascii
from datetime import UTC, datetime
from email.utils import getaddresses
from typing import Final

from pydantic import TypeAdapter

from daily_tasks.communications.gmail_message_part import GmailMessagePart
from daily_tasks.communications.gmail_raw_message import GmailRawMessage
from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.message_address import MessageAddress

_SOURCE = "gmail"
_UNKNOWN_SENDER = "unknown@gmail.invalid"
_MESSAGE: Final[TypeAdapter[CommunicationMessage]] = TypeAdapter(CommunicationMessage)


def gmail_message(raw: GmailRawMessage, fetched_at: datetime) -> CommunicationMessage:
    """Return the `CommunicationMessage` for `raw`; plain-text bodies win over HTML."""
    payload = raw.payload if raw.payload is not None else GmailMessagePart()
    headers = {header.name.lower(): header.value for header in payload.headers}
    senders = _addresses(headers.get("from", ""))
    body, body_format = _body(payload)
    fields: dict[str, object] = {
        "id": f"{_SOURCE}:{raw.id}",
        "source": _SOURCE,
        "external_id": raw.id,
        "thread_id": f"gmail-thread:{raw.threadId}",
        "received_at": datetime.fromtimestamp(int(raw.internalDate) / 1000, tz=UTC),
        "from": senders[0] if senders else MessageAddress(name=None, address=_UNKNOWN_SENDER),
        "to": _addresses(headers.get("to", "")),
        "cc": _addresses(headers.get("cc", "")),
        "channel": "email",
        "subject": headers.get("subject") or None,
        "snippet": raw.snippet,
        "body": body,
        "body_format": body_format,
        "attachments": (),
        "url": f"https://mail.google.com/mail/u/0/#all/{raw.threadId}",
        "fetched_at": fetched_at,
    }
    return _MESSAGE.validate_python(fields)


def _addresses(header: str) -> tuple[MessageAddress, ...]:
    return tuple(
        MessageAddress(name=name or None, address=address) for name, address in getaddresses([header]) if address
    )


def _body(part: GmailMessagePart) -> tuple[str, str]:
    plain = _first_text(part, "text/plain")
    if plain is not None:
        return plain, "text"
    html = _first_text(part, "text/html")
    if html is not None:
        return html, "html"
    return "", "text"


def _first_text(part: GmailMessagePart, mime_type: str) -> str | None:
    if part.mimeType == mime_type and not part.filename and part.body is not None and part.body.data:
        return _decode(part.body.data)
    for child in part.parts:
        found = _first_text(child, mime_type)
        if found is not None:
            return found
    return None


def _decode(data: str) -> str | None:
    try:
        return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4)).decode("utf-8", errors="replace")
    except (binascii.Error, ValueError):
        return None
