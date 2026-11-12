"""Responsibility: Map one Slack history message into a canonical CommunicationMessage.
Public interface:
+-- SNIPPET_LENGTH
`-- slack_message(raw, channel, workspace_domain, fetched_at)
"""

from datetime import datetime
from typing import Final

from pydantic import TypeAdapter

from daily_tasks.communications.slack_channel import SlackChannel
from daily_tasks.communications.slack_raw_message import SlackRawMessage
from daily_tasks.communications.slack_timestamp import slack_timestamp
from daily_tasks.core.communications.communication_message import CommunicationMessage
from daily_tasks.core.communications.message_address import MessageAddress

SNIPPET_LENGTH: Final = 200
_MESSAGE: Final[TypeAdapter[CommunicationMessage]] = TypeAdapter(CommunicationMessage)


def slack_message(
    raw: SlackRawMessage, channel: SlackChannel, workspace_domain: str | None, fetched_at: datetime
) -> CommunicationMessage:
    """Return the `CommunicationMessage` for `raw` read from `channel`."""
    external_id = f"{channel.id}:{raw.ts}"
    thread_ts = raw.thread_ts or raw.ts
    fields: dict[str, object] = {
        "id": f"slack:{external_id}",
        "source": "slack",
        "external_id": external_id,
        "thread_id": f"slack-thread:{channel.id}:{thread_ts}",
        "received_at": slack_timestamp(raw.ts),
        "from": MessageAddress(name=_sender_name(raw), address=raw.user or raw.username or "unknown"),
        "to": (),
        "cc": (),
        "channel": channel.name,
        "subject": None,
        "snippet": _snippet(raw.text),
        "body": raw.text,
        "body_format": "text",
        "attachments": (),
        "url": _permalink(workspace_domain, channel.id, raw.ts),
        "fetched_at": fetched_at,
    }
    return _MESSAGE.validate_python(fields)


def _sender_name(raw: SlackRawMessage) -> str | None:
    profile = raw.user_profile or {}
    for key in ("real_name", "display_name"):
        value = profile.get(key)
        if isinstance(value, str) and value:
            return value
    return raw.username


def _snippet(text: str) -> str:
    collapsed = " ".join(text.split())
    if len(collapsed) <= SNIPPET_LENGTH:
        return collapsed
    return collapsed[: SNIPPET_LENGTH - 1].rstrip() + "…"


def _permalink(workspace_domain: str | None, channel_id: str, ts: str) -> str | None:
    if not workspace_domain:
        return None
    return f"https://{workspace_domain}.slack.com/archives/{channel_id}/p{ts.replace('.', '')}"
