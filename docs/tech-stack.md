# Tech Stack

Record high-level technology context for planning. Keep this file descriptive.

## Stack Summary

Daily Tasks is a Python Hybrid Plugin (encapsulated agent skill facade + MCP server):
- **Encapsulated facade skill** (`skills/daily-tasks/SKILL.md` + `workflows/*.md` + `references/*.md` + `assets/*.md`) authored in Markdown with generated `harness-adapter` manifests and staged distribution bundles (`.temp/dist/`).
- **Deterministic Python Planning Session MCP Server** (`src/daily_tasks/*`, Scale B SOLID Modular Monolith) implementing the 3-screen planning session state machine, Concrete Syntax Tree (CST) non-destructive Markdown parser/writer, role-named collaborator contracts (`ProjectPlanRepository`, `DailyPlanRepository`, `FileStore`, `CommunicationClient`, `SuggestionsRepository`, `CursorStore`, `PlanningDispatcher`), entity-first implementations (`ProjectPlanRepositoryMarkdown`, `DailyPlanRepositoryMarkdown`, `FileStoreLocal`, `CommunicationClientGmail`, `CommunicationClientSlack`, `SuggestionsRepositoryJson`, `CursorStoreJson`), deterministic message pre-matching, and stdio Model Context Protocol (MCP) transport with zero server-side LLM calls.

## Languages and Runtimes

- **Python**: Python `>=3.12`, managed via `uv` and `pyproject.toml` (`hatchling` build backend).

## Frameworks and Services

- **Model Context Protocol (MCP)**: Stdio JSON-RPC 2.0 server (`daily-tasks-mcp`) exposing deterministic planning session and setup tools to MCP hosts (such as Codex, Claude, Cursor, Hermes, and Antigravity) where the host model performs natural-language reasoning and the server validates and persists state.
- **Pydantic (`>=2.10`)**: Immutable, strictly validated domain records and boundary payloads (`pydantic.dataclasses` with `UUID7` and RFC 8259 JSON compliance) matching `docs/specs/*.json`, discriminated by `RecordKind` (`record_kind`).
- **NyssaAI Foundation Packages**:
  - `nyssa-ai-result`: Explicit `Result[T, Error]` error handling across repositories, parsers, and session operations.
  - `nyssa-ai-configuration`: Layered configuration resolved strictly via `user_home` (`~/.nyssa-ai/daily-tasks/`) -> `repo_root` (`<repo_root>/.nyssa-ai/daily-tasks/`), `KeyringInMemory` secret holding, OAuth token management, and sensitive field masking.
  - `nyssa-ai-logging`: Structured diagnostic logging directed strictly to `sys.stderr` so `sys.stdout` remains pure for MCP JSON-RPC frames.
- **Communication Clients (`langchain-core` / Optional Extras & Host-Connected Pass-Through)**:
  - Read-only Gmail (`CommunicationClientGmail` with OAuth 2.0 `gmail.readonly` scope), read-only Slack (`CommunicationClientSlack`), and host-delegated communication pass-through (`daily_tasks_get_fetch_window` + `daily_tasks_start_session(messages=...)`) behind `CommunicationClient`, sharing `<runtime_root>/fetch-cursors.json` and a configurable `initial_lookback_days` setting (defaulting to `7` days on the first pull).
- **Harness Adapters & Staged Bundles**: Tracked root `harness-adapter` manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.mcp.json`, `mcp.json`, `harness-adapters/hermes/`) and gitignored staged bundles (`.temp/dist/portable`, `.temp/dist/cowork`, `.temp/dist/antigravity`, `.temp/dist/hermes`).

## 5-Root Persistence & Artifacts

- **Canonical Work Records (`vault_root`)**: Obsidian/PARA-compatible or plain-folder Markdown files with YAML scalar frontmatter (`state:`), wiki-links, and hidden HTML comment IDs (`<!-- id: UUIDv7 -->`, `<!-- ref: UUIDv7 -->`), containing zero `.nyssa-ai/` files:
  - Projects: `1-projects/YYYY.MM.DD-<slug>/project-index.md`
  - Milestones: `1-projects/YYYY.MM.DD-<slug>/mN-<slug>/mN-<slug>.md`
  - Tasks: `1-projects/YYYY.MM.DD-<slug>/mN-<slug>/tN-<slug>.md`
  - Blockers: `1-projects/YYYY.MM.DD-<slug>/blockers/bN-<slug>.md`
  - Daily Plans: `2-areas/daily-plans/YYYY.MM.DD-daily-plan.md`
- **Configuration (`user_home` -> `repo_root`)**:
  - User profile & OAuth/vault credentials: `~/.nyssa-ai/daily-tasks/` (`profile.json` with per-vault `"vaults"` map)
  - Optional repo profile: `<repo_root>/.nyssa-ai/daily-tasks/profile.json`
- **Mutable Operational State (`runtime_root`)**:
  - Resolved via `--runtime-root` -> `NYSSA_RUNTIME_ROOT` -> `cwd` (`SOUL.md` + `IDENTITY.md`) -> configured `runtimeRoot` / `~/.nyssa-ai/daily-tasks/runtime/`
  - Holds `fetch-cursors.json`, `suggestions.json`, `decision-log.json`, `sessions/YYYY.MM.DD.json`, `.venv/`, and `.temp/`

## Tooling

- **Python & Packaging Commands**:
  - `python -m pytest test/unit test/use_case`: Runs unit, architectural boundary (`ModuleBoundaryTests`), and use-case tests.
  - `python -m mypy --strict src` & `python -m ruff check .`: Runs strict static type-checking (`mypy --strict` with `pydantic.mypy`) and linting.
  - `python scripts/assemble.py write` & `python scripts/assemble.py check`: Regenerates and checks `harness-adapter` manifests and `.temp/dist/` bundles from canonical `skills/` and `src/`.
  - `python scripts/validate.py`: Validates skill frontmatter, relative Markdown links, path hygiene, and version parity.

## Constraints and Unknowns

- **Zero Server-Side LLM Calls**: The Python MCP server is 100% deterministic (`asyncio` state machine, regex/token pre-matching) and requires no LLM API keys; no `langgraph` or `dspy` is used.
- **Non-Destructive Markdown Preservation**: All record mutations preserve unrelated lines, whitespace, user notes, and comments byte-for-byte via the CST engine, writing only after explicit user adjudication.
