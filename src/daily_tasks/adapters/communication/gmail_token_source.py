# Responsibility: Define how the Gmail connector obtains a bearer access token.
# Public interface:
# `-- GmailTokenSource
#     `-- access_token()
"""Token source contract; `GmailOauth` satisfies it with sealed, auto-refreshed grants."""

from typing import Protocol

from nyssa_ai_result import Result

from daily_tasks.domain import SecretString


class GmailTokenSource(Protocol):
    """Returns a currently valid `gmail.readonly` access token, refreshing it headlessly when needed."""

    def access_token(self) -> Result[SecretString]:
        """Return the access token; fails with `Forbidden` when interactive sign-in is required."""
        ...
