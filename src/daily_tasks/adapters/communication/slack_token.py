# Responsibility: Resolve the Slack read token into memory from the environment or the keyring-protected store.
# Public interface:
# +-- SLACK_TOKEN_ENV_VAR
# `-- slack_token(resolver, namespace, key, env_var)
"""Slack token lookup; the token is never read from a plaintext file."""

from typing import Final

from nyssa_ai_result import Result

from daily_tasks.credentials import SecretResolver
from daily_tasks.domain import SecretString

SLACK_TOKEN_ENV_VAR: Final = "SLACK_BOT_TOKEN"


def slack_token(
    resolver: SecretResolver, namespace: str = "communication", key: str = "slack", env_var: str = SLACK_TOKEN_ENV_VAR
) -> Result[SecretString]:
    """Return the token from `env_var`, else the sealed `(namespace, key)` entry.

    Fails with `NotFound` when neither holds a value; the resolver logs the outcome.
    """
    return resolver.resolve(namespace, key, env_var=env_var)
