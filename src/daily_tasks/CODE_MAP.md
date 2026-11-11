# Code Map: `daily_tasks`
## 1. Upward Ingress
None (Top-level entry point or independent root package).

---

## 2. Local Interface & Public Surface
* **Responsibility**: Mark the Daily Tasks Python package root.

```text
__init__.py
`-- (no public symbols)

cli.py
|-- def cli( argv: Sequence[str] | None = None, environ: Mapping[str, str] | None = None, stdin: TextIO | None = None, stdout: TextIO | None = None, ) -> int
`-- main: Final

launch_mcp.py
|-- PLUGIN_ROOT: Final
|-- SRC_DIR: Final
|-- def launch( argv: Sequence[str] | None = None, which_uv: Callable[[str], str | None] = shutil.which, exec_uv: Callable[[str, Sequence[str]], int] = _default_exec, ) -> int
`-- def main() -> int

logging_setup.py
|-- LOG_LEVEL_ENV_VAR: Final = "DAILY_TASKS_LOG_LEVEL"
`-- def logging_setup( environ: Mapping[str, str], file_path: str | None = None, provider_factory: Callable[[str | None, str], LoggerProvider] | None = None, ) -> logging.Logger
```

---

## 3. Sub-Packages (1 Tier Down)
| Sub-Directory | Responsibility | Map Link |
| :--- | :--- | :--- |
| `adapters/` | Group the port adapter implementations. | [adapters/CODE_MAP.md](adapters/CODE_MAP.md) |
| `auth/` | Group the interactive sign-in entry points for communication sources. | [auth/CODE_MAP.md](auth/CODE_MAP.md) |
| `credentials/` | Expose runtime secret resolution, out-of-band capture and vault registration for credentials. | [credentials/CODE_MAP.md](credentials/CODE_MAP.md) |
| `domain/` | Expose the domain DTO boundary API. | [domain/CODE_MAP.md](domain/CODE_MAP.md) |
| `graph/` | Expose the state graph build boundary API. | [graph/CODE_MAP.md](graph/CODE_MAP.md) |
| `matching/` | Expose deterministic message pre-matching, signal detection and draft suggestion generation. | [matching/CODE_MAP.md](matching/CODE_MAP.md) |
| `ports/` | Expose the runtime port contracts the planning session reads and writes through. | [ports/CODE_MAP.md](ports/CODE_MAP.md) |
| `server/` | Expose the MCP stdio server that drives the deterministic planning session. | [server/CODE_MAP.md](server/CODE_MAP.md) |
| `session/` | Expose the planning session lifecycle, row resolution, screen rendering and adjudication. | [session/CODE_MAP.md](session/CODE_MAP.md) |
| `storage/` | Group the Markdown record storage features. | [storage/CODE_MAP.md](storage/CODE_MAP.md) |
