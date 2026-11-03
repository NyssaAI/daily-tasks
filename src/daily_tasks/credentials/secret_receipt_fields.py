# Responsibility: Turn a sanitized secret receipt into plain JSON-safe fields.
# Public interface:
# `-- secret_receipt_fields(receipt)
"""Receipt projection shared by logs, the MCP reply and CLI output; it carries no secret value."""

from datetime import UTC

from nyssa_ai_configuration import SecretReceipt


def secret_receipt_fields(receipt: SecretReceipt) -> dict[str, str]:
    """Return `namespace`, `key`, `provider` and `stored_at` (UTC ISO 8601 ending in `Z`)."""
    stored_at = receipt.stored_at.astimezone(UTC).isoformat(timespec="seconds").replace("+00:00", "Z")
    return {"namespace": receipt.namespace, "key": receipt.key, "provider": receipt.provider, "stored_at": stored_at}
