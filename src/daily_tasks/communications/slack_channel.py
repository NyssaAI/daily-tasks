"""Responsibility: Name one Slack conversation the connector reads.
Public interface:
`-- SlackChannel
    +-- id
    `-- name

Configured Slack conversation: a public/private channel or a direct message.
"""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True)
class SlackChannel:
    """Slack conversation ID (`C...`, `G...`, `D...`) and the display name used as `Message.channel`."""

    id: str
    name: str
