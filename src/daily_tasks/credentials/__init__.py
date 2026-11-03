# Responsibility: Expose runtime secret resolution for adapter credentials.
# Public interface:
# (none)
"""In-memory credential resolution backed by the environment and the keyring-protected configuration store."""

from daily_tasks.credentials.secret_logger import SecretLogger
from daily_tasks.credentials.secret_resolver import SecretResolver

__all__ = ["SecretLogger", "SecretResolver"]
