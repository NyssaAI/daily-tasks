# Responsibility: Validate one message object returned by Slack `conversations.history`.
# Public interface:
# `-- SlackRawMessage
#     +-- subtype
#     +-- text
#     +-- thread_ts
#     +-- ts
#     +-- user
#     +-- user_profile
#     `-- username
"""Slack message wire shape; fields the connector does not use are ignored."""

from collections.abc import Mapping

from pydantic import ConfigDict, Field, JsonValue
from pydantic.dataclasses import dataclass


@dataclass(frozen=True, slots=True, kw_only=True, config=ConfigDict(extra="ignore"))
class SlackRawMessage:
    """Message as Slack sends it; `ts` is the epoch timestamp string that identifies it per channel."""

    ts: str = Field(pattern=r"^\d+(\.\d{1,6})?$")
    text: str = ""
    user: str | None = None
    username: str | None = None
    subtype: str | None = None
    thread_ts: str | None = None
    user_profile: Mapping[str, JsonValue] | None = None
