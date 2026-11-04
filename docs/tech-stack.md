# Tech Stack

Record high-level technology context for planning. Keep this file descriptive.

## Stack Summary

Daily Tasks is a Python plugin and skill suite:
- **Six canonical agent skills** (`skills/daily-tasks*`) authored in Markdown with generated host-specific manifests and distribution bundles (`artifacts/`).
- **Deterministic Python Planning Session MCP Server** (`src/daily_tasks/*`) implementing the 3-screen planning session state machine, Concrete Syntax Tree (CST) surgical Markdown parser/writer, pluggable read-only ports (`ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`, `LocalFileStore`), deterministic message pre-matching, and stdio Model Context Protocol (MCP) transport with zero server-side LLM calls.

## Languages and Runtimes

- **Python**: Python `>=3.12`, managed via `uv` and `pyproject.toml` (`hatchling` build backend).

## Frameworks and Services

- **Model Context Protocol (MCP)**: Stdio JSON-RPC 2.0 server (`daily-tasks-mcp`) exposing deterministic planning session tools to MCP hosts (such as Codex, Claude, Cursor, and Antigravity) where the host model performs natural-language reasoning and the server validates and persists state.
- **Pydantic (`>=2.10`)**: Immutable, strictly validated domain DTOs (`pydantic.dataclasses` with `UUID7` and RFC 8259 JSON compliance) matching `docs/specs/*.json`.
- **NyssaAI Foundation Packages**:
  - `nyssa-ai-result`: Explicit `Result[T, Error]` error handling across ports, parsers, and session operations.
  - `nyssa-ai-configuration`: Layered configuration, `KeyringInMemory` secret holding, OAuth token management, and sensitive field masking.
  - `nyssa-ai-logging`: Structured diagnostic logging directed strictly to `sys.stderr` so `sys.stdout` remains pure for MCP JSON-RPC frames.
- **Communication Connectors (`langchain-core` / Optional Extras & Host-Connected Pass-Through)**:
  - Read-only Gmail (`GmailConnector` with OAuth 2.0 `gmail.readonly` scope), read-only Slack (`SlackConnector`), and host-delegated communication ingestion (`HarnessCommunicationAdapter` / `daily_tasks_get_fetch_window` + `daily_tasks_start_session(messages=...)`) behind `CommunicationPort`, sharing `<state_root>/fetch-cursors.json` and a configurable `initial_lookback_days` setting (defaulting to `7` days on the first pull).
- **Host Adapters**: Portable bundle (`artifacts/portable`), Cowork bundle (`artifacts/cowork`), and Antigravity/Hermes adapters (`artifacts/antigravity`, `artifacts/hermes`).

## Storage and Artifacts

- **Canonical Work Records**: Obsidian/PARA-compatible or plain-folder Markdown files with YAML scalar frontmatter, wiki-links, and hidden HTML comment IDs (`<!-- id: UUIDv7 -->`, `<!-- ref: UUIDv7 -->`):
  - Projects: `projects/YYYY.MM.DD-<slug>/project-index.md`
  - Milestones: `projects/YYYY.MM.DD-<slug>/mN-<slug>/mN-<slug>.md`
  - Tasks: `projects/YYYY.MM.DD-<slug>/mN-<slug>/tN-<slug>.md`
  - Blockers: `projects/YYYY.MM.DD-<slug>/blockers/bN-<slug>.md`
  - Daily Plans: `daily-plans/YYYY.MM.DD-daily-plan.md` (or `{vault root}/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md` in PARA layouts)
- **Configuration & Operating State**:
  - User profile: `~/.nyssa-ai/daily-tasks/profile.json`
  - Workspace profile & operating state: `<workspace root>/.nyssa-ai/daily-tasks/` (`profile.json`, `fetch-cursors.json`, `suggestions.json`, `decision-log.json`, `sessions/YYYY.MM.DD.json`)
  - Persisted messages and message log: `<messages_root>/YYYY-MM-DD/<source>/<id>/message.json` and `<messages_root>/message-log.json`

## Tooling

- **Python & Packaging Commands**:
  - `python -m pytest test/unit`: Runs unit and integration tests under `test/unit/daily_tasks/`.
  - `python -m mypy --strict src` & `ruff check`: Runs strict static type-checking (`mypy --strict` with `pydantic.mypy`) and linting.
  - `python .nyssa-ai/dev-standards/python/scripts/check_adoption.py . --run`: Validates Python architectural and file/header standards (`PY-FILE`, `PY-HEADER`).
  - `python scripts/assemble.py write` & `python scripts/assemble.py check`: Regenerates and checks host manifests and distribution bundles from canonical `skills/` and `src/`.
  - `python scripts/validate.py`: Validates skill frontmatter, relative Markdown links, path hygiene, and version parity.

## Constraints and Unknowns

- **Zero Server-Side LLM Calls**: The Python MCP server is 100% deterministic (`asyncio` state machine, regex/token pre-matching) and requires no LLM API keys; no `langgraph` or `dspy` is used.
- **Surgical Markdown Preservation**: All record mutations must preserve unrelated lines, whitespace, user notes, and comments byte-for-byte via the CST engine, only writing after explicit user adjudication.
