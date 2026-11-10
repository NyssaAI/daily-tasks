"""Responsibility: Define the sealed OAuth grant storage Gmail sign-in needs.
Public interface:
`-- GmailTokenStore
    +-- authorize(namespace, key, options, browser_launcher)
    `-- get(namespace, key)

Covering contract over `nyssa_ai_configuration.ConfigurationClient` OAuth entries.
"""

from typing import Protocol

from nyssa_ai_configuration import BrowserLauncher, OAuthOptions
from nyssa_ai_result import Result


class GmailTokenStore(Protocol):
    """Stores grants only sealed with the keyring-held master key; reads refresh expiring grants."""

    def authorize(
        self, namespace: str, key: str, options: OAuthOptions, browser_launcher: BrowserLauncher | None = None
    ) -> Result[None]:
        """Run the interactive PKCE sign-in and seal the grant at (namespace, key)."""
        ...

    def get(self, namespace: str, key: str) -> Result[str]:
        """Return the access token at (namespace, key), refreshing it when it expires within 5 minutes."""
        ...
