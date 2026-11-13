# Daily Tasks

Public NyssaAI Hybrid Plugin (encapsulated `skills/daily-tasks/` facade + deterministic Python MCP server).
Maintain canonical instructions under `skills/`; host files (`harness-adapters/`, `.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.mcp.json`, `mcp.json`) are thin generated `harness-adapter` manifests.
This is a skill collection, not an agent persona. Never add time fitting or implicit acceptance.
Anchor all domain nouns, state transitions, and boundary contracts to the Ubiquitous Language in
`docs/GLOSSARY.md`, `docs/concepts/`, and `docs/specs/`; strictly ban naming drift and unvetted synonyms.

## 5-Root Model & Configuration Boundaries

- **`user_home` (`~`)**: Owns `~/.nyssa-ai/daily-tasks/config.json` (`NyssaAI.Configuration` precedence #1, with read-only legacy fallback to `profile.json`).
- **`repo_root`**: Owns `AGENTS.md`, `docs/`, `src/`, `test/`, single root `.temp/` (including `.temp/dist/` staged bundles), and optional `<repo_root>/.nyssa-ai/daily-tasks/config.json` (`NyssaAI.Configuration` precedence #2). Never assemble or self-load plugin trees (`.agents/`, `.hermes/`, `artifacts/`) inside `repo_root`.
- **`vault_root`**: User or shared PARA/non-PARA work-record vault (`projectsRoot` defaults to `1-projects`, `dailyPlansRelative` defaults to `2-areas/daily-plans`). **Zero `.nyssa-ai/` files or runtime state may ever be read from or written inside `vault_root`**, and agent persona runtime directories (`SOUL.md` + `IDENTITY.md`) are rejected as `vault_root`.
- **`runtime_root`**: Mutable operational state (`fetch-cursors.json`, `suggestions.json`, `decision-log.json`, `sessions/`, opt-in `usage/events.jsonl`, `.venv/`, and runtime `.temp/`), resolved deterministically: (1) `--runtime-root` -> (2) `NYSSA_RUNTIME_ROOT` -> (3) `<cwd>/.nyssa-ai/daily-tasks/runtime/` when `cwd` contains `SOUL.md` + `IDENTITY.md` -> (4) configured `runtimeRoot`, `<repo_root>/.nyssa-ai/daily-tasks/runtime/`, or `~/.nyssa-ai/daily-tasks/runtime/`.
- **`plugin_root`**: Read-only installed or source plugin bundle directory.

## Scale B SOLID Modular Monolith (`src/daily_tasks/`)

Python (`>=3.12`, managed with `uv` via `pyproject.toml`) is the sole runtime language:
- `src/daily_tasks/core/{records,communications,planning}/`: Pure, OS- and transport-free domain entities, immutable state transitions, message correlation, 3-screen planning pipeline, and consumer-owned **Role-Named Collaborator Contracts** (`ProjectPlanRepository`, `DailyPlanRepository`, `FileStore`, `CommunicationClient`, `SuggestionsRepository`, `CursorStore`, `PlanningDispatcher`). Zero imports from `os`, `pathlib`, `mcp`, `httpx`, `nyssa_ai_*`, or outer slices.
- `src/daily_tasks/{records,communications,planning}/`: Independent capability slices owning **Entity-First** implementations (`ProjectPlanRepositoryMarkdown`, `DailyPlanRepositoryMarkdown`, `FileStoreLocal`, `CommunicationClientGmail`, `CommunicationClientSlack`, `SuggestionsRepositoryJson`, `CursorStoreJson`, `DecisionLogStoreJson`, `SessionCommitterLocal`) with zero sibling cross-imports.
- `src/daily_tasks/transports/mcp/`: Thin stdio MCP server adapter translating JSON-RPC tool calls into `PlanningDispatcher`, `SetupHandler`, and `SecretCapturer`.
- `src/daily_tasks/hosting/`: `ServerSettings` / `ProfileStore` / `resolve_runtime_root` configuration resolution and composition root (`compose_mcp_server`).

The Daily Tasks planning session MCP server must ONLY be invoked by agents via host MCP tool calls (`daily_tasks_start_session`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_confirm_plan`, `daily_tasks_get_session_state`, `daily_tasks_cancel_session`, `daily_tasks_configure_vault`, `daily_tasks_capture_secret`). Never execute `daily-tasks-mcp` or `python -m daily_tasks` as an agent shell subprocess during workflows.

If vault setup is not already done, trigger and complete setup (`skills/daily-tasks/workflows/setup.md`) before attempting planning, check-in, or record management. Fix malformed files using `skills/daily-tasks/workflows/records.md` while preserving notes and formatting intact.

## Development & Verification Standards

- **Ubiquitous Language & Naming (`ARCH-NAME`, `ARCH-DATA`)**: Ground every symbol in `docs/GLOSSARY.md`. Horizontal grab-bag folders (`adapters/`, `ports/`, `domain/`, `storage/`, etc.) and technical suffixes (`*DTO`, `*Dto`, `*Schema`, `*Model`, `*Input`, `*Output`, `*Class`, `*Type`, `*Object`, `*Data`, `*Port`, `*Protocol`, `*SourceRead`) are strictly banned and enforced by AST checkers and `test/unit/architecture/test_module_boundaries.py`.
- **Code Navigation (`docs/code-map/codegraph.db`)**: Query the tracked CodeGraph AST snapshot via `codegraph_explore` before running broad recursive searches. Regenerate after `src/` structural changes with `node <dev-standards>/skills/dev-standards/scripts/codegraph-mcp.mjs --snapshot .`.
- **Verification Suite**:
  ```text
  .venv/bin/python -m mypy --strict src
  .venv/bin/python -m ruff check .
  .venv/bin/python -m pytest
  .venv/bin/python scripts/assemble.py write
  .venv/bin/python scripts/assemble.py check
  .venv/bin/python scripts/validate.py
  ```

# Development standards (python)
<!-- dev-standards: language=python version=0.10.8 revision=cff6156b186231685082c79becccf1db2c30abed sha256=76dca372404769e0cc8a86356c40b6cd9100fde24fc4d5becbacb0a54bbe10d5 -->

- **Ubiquitous Language**: Ground all domain concepts, variables, boundary DTOs, and state transitions in the project's authoritative Ubiquitous Language (`docs/GLOSSARY.md` or `docs/concepts/`, and `apps/<app>/docs/GLOSSARY.md` + root Context Map in a monorepo). Banned synonyms and naming drift are strictly prohibited (`ARCH-NAME`).
- **Code Navigation (`CodeGraph`)**: Reach for `codegraph_explore` (bundled in the `dev-standards` MCP server, or `codegraph explore "<query>"` via CLI) backed by the pre-indexed `docs/code-map/codegraph.db` snapshot (`apps/<app>/docs/code-map/codegraph.db` and `tools/<tool>/docs/code-map/codegraph.db` in a monorepo) before executing recursive file searches (`find`, `dir`, globbing) or broad repository greps (`rg`, `Select-String`). Never generate `CODE_MAP.md` files; refresh snapshots after structural symbol changes with `--sync-codegraph`.
- **Repository & Architecture Standards**: Follow the external `dev-standards` plugin (`nyssa-ai/dev-standards`) rules in `<plugin_root>/skills/dev-standards/rules/repo-standards.md`, `<plugin_root>/skills/dev-standards/rules/architecture-standards.md`, and `<plugin_root>/skills/dev-standards/rules/python-standards.md` before changing owned Python code or `repo_root` layout (`src/`, `test/unit/`, `test/use_case/`, Allowed-Set `docs/` with `docs/GLOSSARY.md` and `docs/specs/*.json` only, single root `.temp/`, and `user_home` -> `repo_root` `.nyssa-ai/` config with gitignored `.nyssa-ai/*/runtime/`). Structure `src/` as a Scale A capability suite (`src/<capability>/`) or Scale B multi-transport modular monolith (transport-free `core/<concept>/` with inward boundaries, independent `<feature>/` slices, thin `transports/<protocol>/`, `hosting/`), using Role-Named Collaborator Contracts (no `*Port`, `*Protocol`, or `I` prefix) and Entity-First Implementations (`<Role><Mechanism>`); never create horizontal grab-bag directories (`adapters`, `ports`, `storage`, `contracts`, `shared`, `utils`, `helpers`, `common`, `misc`, `types`, `models`) or plumbing DTO suffixes (`*DTO`, `*Dto`, `*Schema`, `*Model`, `*Input`, `*Output`, `*Class`, `*Type`, `*Object`, `*Data`). Write a module-docstring `Responsibility: <summary>` on authored modules and auto-generate/sync `Public interface:` ASCII trees with `--update-headers` rather than hand-editing trees (`ARCH-HEADER`). Do not store or commit `dev-standards` bundles, `.agents/`, `.hermes/`, or `artifacts/` inside `repo_root`. Repository requirements and explicit user instructions take precedence; record the scope and reason of an exception in the change description.
- **References & Examples**: Read relevant `dev-standards` Python references under `<plugin_root>/skills/dev-standards/references/python/` (`logging.md`, `testing.md`, `code-smells.md`, and `examples/`) when designing operational boundaries, tests, or evaluating code smells with source evidence and counterexamples.
- **Verification & Adoption**: Run applicable `mypy --strict`, `pytest test/unit`, and `pytest test/use_case` commands locally. Unit tests must work without Docker; requested infrastructure tests require Docker and must report missing prerequisites as blocked, never as a pass. Use the external structural checker (`src/python/check.py` and `src/python/check_adoption.py` from `<plugin_root>`) as local feedback and report unsupported coverage separately from rule violations:

```text
python <plugin_root>/src/python/check_adoption.py .
python <plugin_root>/src/python/check_adoption.py . --sync
python <plugin_root>/src/python/check_adoption.py . --update-headers
python <plugin_root>/src/python/check_adoption.py . --sync-codegraph
python <plugin_root>/src/python/check_adoption.py . --run
```
