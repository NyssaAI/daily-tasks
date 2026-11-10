# Code Map: `credentials`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
Immediate caller and integration context:
* **Caller**: [`../cli.py`](../cli.py) -> `cli`
* **Caller**: [`../adapters/communication/slack_token.py`](../adapters/communication/slack_token.py) -> `slack_token`
* **Caller**: [`../auth/gmail.py`](../auth/gmail.py) -> `gmail`

---

## 2. Local Interface & Public Surface
* **Responsibility**: Expose runtime secret resolution, out-of-band capture and vault registration for credentials.

```text
__init__.py
`-- (no public symbols)

secret_capture_service.py
`-- class SecretCaptureService
    |-- def __init__( self, writer: ConfigurationSecretWriter, input_provider: SecretInputProvider | None = None, status_out: TextIO | None = None, ) -> None
    `-- def capture( self, namespace: str, key: str, prompt_message: str | None = None, preferred_provider: str | None = None, forced_provider: str | None = None, mode: SecretCaptureMode = SecretCaptureMode.AUTO, timeout_seconds: float = 120.0, ) -> Result[SecretReceipt]

secret_receipt_fields.py
`-- def secret_receipt_fields(receipt: SecretReceipt) -> dict[str, str]

secret_resolver.py
`-- class SecretResolver
    |-- def __init__(self, reader: ConfigurationReader, environ: Mapping[str, str]) -> None
    `-- def resolve(self, namespace: str, key: str, env_var: str | None = None) -> Result[SecretString]

vault_registry.py
`-- class VaultRegistry
    |-- def __init__(self, factories: Iterable[CloudKeyVaultFactory] = ()) -> None
    |-- def register(self, factory: CloudKeyVaultFactory) -> "VaultRegistry"
    |-- def factories(self) -> tuple[CloudKeyVaultFactory, ...]
    |-- def kinds(self) -> tuple[str, ...]
    `-- def find(self, kind: str) -> Result[CloudKeyVaultFactory]
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
