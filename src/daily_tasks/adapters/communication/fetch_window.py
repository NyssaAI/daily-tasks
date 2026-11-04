# Responsibility: Represent the fetch bounds of one communication source for the next pull.
# Public interface:
# `-- FetchWindow
#     +-- after_epoch
#     +-- has_cursor
#     +-- initial_lookback_days
#     +-- last_external_id
#     +-- since
#     `-- source
"""FetchWindow DTO: what a connector or an assistant harness connection must read next."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True, kw_only=True)
class FetchWindow:
    """Messages newer than `since` are new; on a first pull (`has_cursor` false) `since` itself is included.

    `after_epoch` is `since` in whole Unix seconds (Gmail `after:`); `last_external_id` is already processed.
    """

    source: str
    has_cursor: bool
    since: datetime
    after_epoch: int
    last_external_id: str | None
    initial_lookback_days: int
