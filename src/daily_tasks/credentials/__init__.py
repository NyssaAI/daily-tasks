"""Responsibility: Expose runtime secret resolution, out-of-band capture and vault registration for credentials.
Public interface:
(none)

In-memory credential resolution backed by the environment and the keyring-protected configuration store.
"""

from daily_tasks.credentials.secret_capture_service import SecretCaptureService
from daily_tasks.credentials.secret_receipt_fields import secret_receipt_fields
from daily_tasks.credentials.secret_resolver import SecretResolver
from daily_tasks.credentials.vault_registry import VaultRegistry

__all__ = ["SecretCaptureService", "SecretResolver", "VaultRegistry", "secret_receipt_fields"]
