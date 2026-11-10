# Code Map: `auth`
[Up: daily_tasks](../CODE_MAP.md)

## 1. Upward Ingress
None (Top-level entry point or independent root package).

---

## 2. Local Interface & Public Surface
* **Responsibility**: Group the interactive sign-in entry points for communication sources.

```text
__init__.py
`-- (no public symbols)

gmail.py
|-- APPLICATION_NAME: Final = "daily-tasks"
|-- CLIENT_ID_ENV_VAR: Final = "GMAIL_CLIENT_ID"
|-- CLIENT_SECRET_ENV_VAR: Final = "GMAIL_CLIENT_SECRET"
|-- def gmail( argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None, keyring: Keyring | None = None, http_post: Callable[[str, Mapping[str, str]], Result[tuple[int, str]]] | None = None, browser_launcher: BrowserLauncher | None = None, out: TextIO | None = None, ) -> int
`-- main: Final

secret.py
|-- APPLICATION_NAME: Final = "daily-tasks"
|-- main: Final
`-- def secret( argv: Sequence[str] | None = None, keyring: Keyring | None = None, vault_registry: VaultRegistry | None = None, input_provider: SecretInputProvider | None = None, out: TextIO | None = None, status_out: TextIO | None = None, ) -> int
```

---

## 3. Sub-Packages (1 Tier Down)
*None (leaf module directory).*
