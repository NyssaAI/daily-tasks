# Daily Tasks

Public NyssaAI plugin. Maintain canonical instructions under `skills/`; host files
are thin generated manifests. This is a skill collection, not an agent persona.
Never add time fitting, or implicit acceptance.
Anchor all domain nouns, state transitions, and boundary contracts to the Ubiquitous Language in
`docs/GLOSSARY.md`, `docs/CONCEPTS.md`, and `docs/specs/`; strictly ban naming drift and unvetted synonyms.

Python (>=3.12, managed with `uv` via `pyproject.toml`) is the sole runtime language.
Python code lives under `src/daily_tasks/` and is tested with `pytest`. Python
dependencies are limited to `lang*` packages (e.g. `langchain-*`) and `nyssa-ai`
packages, plus others only when a concrete need requires one. Keep scratch in `.temp/`.
Public behavior is documented in `README.md` and `skills/`; never include personal records or credentials.
Regenerate manifests/artifacts with `python scripts/assemble.py write`, then check with `python scripts/assemble.py check` and `python scripts/validate.py`.
Do not claim host activation from packaging or direct CLI tests.

The log is script-only. Other Markdown writes belong to skills, except for the
deterministic Daily Tasks planning session MCP server whose LocalFileStore is
authorized to apply validated record changes and daily plans exclusively following
explicit user adjudication; integrity code validates, compares and proposes changes
without owning the full workflow.
The Daily Tasks planning session MCP server must ONLY be used via MCP (through host
MCP tool calls: `daily_tasks_start_session`, `daily_tasks_execute_operations`,
`daily_tasks_advance_screen`, `daily_tasks_confirm_plan`, `daily_tasks_get_session_state`,
`daily_tasks_cancel_session`). Never execute `daily-tasks-mcp` or `python -m daily_tasks.server`
as a CLI command or shell subprocess.
If project setup is not already done, trigger and complete setup (`skills/daily-tasks/workflows/setup.md`)
before attempting planning, check-in, or record management.
Fix malformed files using `skills/daily-tasks/workflows/records.md` by repairing frontmatter and structure
while preserving notes and formatting intact.
Keep resolved config, vault and projects roots independent of cwd. Reuse existing
settings before asking for missing scope. User and project configuration and
operating state use canonical `.nyssa-ai/daily-tasks/`; preserve accepted explicit paths.

Scoped `dev-standards` exception (`REPO-GITIGNORE`): `.nyssa-ai/` (including `.nyssa-ai/dev-standards/`)
is intentionally gitignored via `.*` in `.gitignore` because `daily-tasks` is a public NyssaAI plugin
validated by `plugin-builder`, which prohibits tracked non-canonical root dot-directories. Contributors
with `dev-standards` installed populate `.nyssa-ai/dev-standards/` locally via `check_adoption.py . --sync`
and re-strip any auto-appended `!.nyssa-ai/` lines from `.gitignore`.

# Development standards (python)

- **Ubiquitous Language**: Ground all domain concepts, variables, boundary DTOs, and state transitions in the project's authoritative Ubiquitous Language (`GLOSSARY.md` or `docs/concepts/`, and root Context Map in a monorepo). Banned synonyms and naming drift are strictly prohibited (`ARCH-NAME`).
- **Code Navigation (`CODE_MAP.md`)**: Every source directory containing code owns a deterministic `CODE_MAP.md`. Before executing recursive file searches (`find`, `dir`, globbing) or running broad repository greps (`rg`, `Select-String`), always consult the local package `CODE_MAP.md` (and immediate parent `CODE_MAP.md`) to inspect public interfaces, exported symbols, caller expectations, and child packages (`REPO-CODE-MAP`). Regenerate after structural changes with `python scripts/generate_codemaps.py`.

Read `.nyssa-ai/dev-standards/python/rules/repo-standards.md`,
`.nyssa-ai/dev-standards/python/rules/architecture-standards.md` and
`.nyssa-ai/dev-standards/python/rules/standards.md` before changing owned python code or repository layout.
The pinned source revision, owned roots and local commands are recorded in
`.nyssa-ai/dev-standards/python.json`. Repository requirements and explicit user instructions take
precedence; record the scope and reason of an exception in the change description.

Read relevant examples when a design choice needs one. For operational boundaries, also read
`.nyssa-ai/dev-standards/python/references/logging.md`. For tests and fixtures, read
`.nyssa-ai/dev-standards/python/references/testing.md`. Apply relevant entries of
`.nyssa-ai/dev-standards/python/references/code-smells.md` with source evidence and counterexamples.

Run applicable build/typecheck, unit and use-case commands locally. Unit tests must work without Docker.
A requested infrastructure test requires Docker; report missing prerequisites as blocked,
never as a pass. Use the structural checker as local feedback and report unsupported coverage
separately from rule violations. A green checker does not establish complete conformance.
Do not add CI wiring, hooks or automatic standards execution.

Validate adoption with:

```text
python .nyssa-ai/dev-standards/python/scripts/check_adoption.py .
```

Update the pinned local bundle from the installed `dev-standards` plugin with:

```text
python .nyssa-ai/dev-standards/python/scripts/check_adoption.py . --sync
```

Execute the configured local build and unit commands plus the structural checks with `--run`.
Add `--use-case` to run the configured infrastructure suite explicitly. Review command definitions
before executing them; they are owned by this repository.
