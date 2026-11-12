"""Responsibility: Resolve the Slack read token into memory from the environment or the keyring-protected store.
Public interface:
+-- SLACK_TOKEN_ENV_VAR
`-- slack_token(resolver, namespace, key, env_var)
"""

from typing import Final

from nyssa_ai_result import Result

from daily_tasks.communications.secret_resolver import SecretResolver
from daily_tasks.communications.secret_string import SecretString

SLACK_TOKEN_ENV_VAR: Final = "SLACK_BOT_TOKEN"


def slack_token(
    resolver: SecretResolver, namespace: str = "communication", key: str = "slack", env_var: str = SLACK_TOKEN_ENV_VAR
) -> Result[SecretString]:
    """Return the token from `env_var`, else the sealed `(namespace, key)` entry."""
    return resolver.resolve(namespace, key, env_var=env_var)
