# Daily Tasks

Version **0.11.3**

Personal task management and daily planning through an encapsulated `daily-tasks` agent skill,
five focused workflows, and a deterministic Python Model Context Protocol (MCP) planning server.
Maintain projects, milestones, tasks and external blockers in editable Markdown inside your vault;
review your own and delegated work in a local-day plan. The skill provides capabilities to your agent,
without becoming an autonomous assistant persona or fitting work into a timeframe.

## Use

Ask to set up Daily Tasks, capture possible work, update a task, plan the day, or check in.
The entry skill (`skills/daily-tasks/SKILL.md`) loads only the selected workflow. New projects,
milestones and tasks need explicit acceptance; your instruction to create named work supplies that
acceptance. Quoted requests and inferred promises remain candidates. A check-in can happen anytime;
it creates today's missing plan, carries unfinished selected work forward and reconciles
manual checkbox edits.

| Workflow | Path | Purpose |
| --- | --- | --- |
| Entry / Router | `skills/daily-tasks/SKILL.md` | Route a request to the matching workflow |
| Setup | `skills/daily-tasks/workflows/setup.md` | Identity, timezone, priorities, vault bindings and MCP communication setup |
| Capture | `skills/daily-tasks/workflows/capture.md` | Candidate review and explicit acceptance |
| Records | `skills/daily-tasks/workflows/records.md` | Accepted work, delegation, progress, DoD, blockers and malformed-file repair |
| Plan | `skills/daily-tasks/workflows/plan.md` | Daily selections, ownership review and explicit future planning |
| Check-in | `skills/daily-tasks/workflows/checkin.md` | Reconciliation, progress reports and resumable decisions |

## 5-Root Model & Authority

- **Configuration (`user_home` -> `repo_root`)**: Schema Version 2 settings are resolved via `NyssaAI.Configuration` conventions from `~/.nyssa-ai/daily-tasks/config.json` (`user_home`, precedence #1) and `<repo_root>/.nyssa-ai/daily-tasks/config.json` (`repo_root`, precedence #2), with read-only fallback to legacy `profile.json` when `config.json` is absent. Per-vault bindings live under `"vaults"` alongside `defaultVaultRoot` and optional `"telemetry": {"enabled": false}`. **Zero `.nyssa-ai/` files are ever read from or written inside `vault_root`.**
- **Vault (`vault_root`)**: Holds editable Markdown work records for both PARA and non-PARA vaults. Default mappings are `<vault_root>/1-projects` (`projectsRoot`) and `<vault_root>/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md` (`dailyPlansRelative`). Agent persona runtime directories (`SOUL.md` + `IDENTITY.md`) are rejected if passed as `vault_root`.
- **Runtime state (`runtime_root`)**: Mutable operational state (`fetch-cursors.json`, `suggestions.json`, append-only `decision-log.json`, `sessions/`, opt-in `usage/events.jsonl`, `.venv/`, and runtime `.temp/`) lives strictly in `runtime_root`, resolved in order: (1) `--runtime-root` -> (2) `NYSSA_RUNTIME_ROOT` -> (3) `<cwd>/.nyssa-ai/daily-tasks/runtime/` when `cwd` contains `SOUL.md` + `IDENTITY.md` -> (4) configured `runtimeRoot`, `<repo_root>/.nyssa-ai/daily-tasks/runtime/`, or `~/.nyssa-ai/daily-tasks/runtime/`.
- **Project structure**: Project index (`1-projects/YYYY.MM.DD-<slug>/project-index.md`) plus `m1-name/m1-name.md` milestones and sibling `t1-name.md` tasks. Each milestone and task owns its own Definition of Done; tasks also own requirements. Flat milestone `inputs/` and `outputs/` hold files linked by tasks (`project -> milestone -> task -> files`). Project-wide blockers stay in `blockers/`. Work records use `state:` frontmatter (`not-started`, `in-progress`, `completed`, `cancelled`; blockers use `open`, `resolved`) and UUIDv7 `id`. DoD criterion IDs and projection `ref` IDs use hidden comments.
- **Time & ownership**: Store UTC (`Z`), present configured local time with IANA timezone. Human email owner; optional person/agent assignee falling back to owner. Target dates are optional and explicit.

## Runtime and packaging

Python 3.12 or later (managed with `uv` via `pyproject.toml`) runs the deterministic
MCP planning session server (`daily-tasks-mcp`, structured as a Scale B SOLID Modular Monolith under `src/daily_tasks/`).
The planning server is accessed strictly via host MCP tool calls (`daily_tasks_*`); agents never invoke it as a CLI command.
All diagnostic logging goes to `stderr` so `stdout` remains pure for MCP JSON-RPC 2.0 frames.

Daily Tasks enforces a mandatory full-setup gate: downstream workflows (`plan`, `records`, `checkin`,
and `capture`) never run unless `daily_tasks_*` MCP tools are live in the active harness, Schema
Version 2 `config.json` bindings (`vaultRoot`, `projectsRoot`, `dailyPlansRelative`, `user.email`, IANA `timezone`,
and `sources`) are present in `~/.nyssa-ai/daily-tasks/`, and vault templates are initialized. When any setup gate is incomplete,
the skill immediately halts downstream work and runs harness-aware setup (`skills/daily-tasks/workflows/setup.md`
and `skills/daily-tasks/references/harness-setup.md`). Malformed files trigger non-destructive repairs (`skills/daily-tasks/workflows/records.md`).

```text
# Host registration / direct server launch:
uv run daily-tasks-mcp --vault-root /absolute/vault --runtime-root /absolute/runtime
uv run python -m daily_tasks --vault-root /absolute/vault --runtime-root /absolute/runtime
# Out-of-band secrets (masked prompt or loopback page; never pasted into chat):
uv run python -m daily_tasks.communications.secret gmail
uv run python -m daily_tasks.communications.secret vault --name bws --kind bitwarden-secrets --project-id ID
# Gmail OAuth setup:
uv run python -m daily_tasks.communications.gmail --config-dir /absolute/home/.nyssa-ai/daily-tasks
```

See [MCP & CLI contract](skills/daily-tasks/references/cli.md), [record conventions](skills/daily-tasks/references/records.md)
and [reconciliation](skills/daily-tasks/references/operations.md).

Install a host bundle from the [latest release](https://github.com/NyssaAI/daily-tasks/releases/latest),
or stage distribution bundles from source with `python scripts/assemble.py write`. Staged distribution bundles
(`.temp/dist/` — `portable`, `cowork`, `antigravity`, and `hermes`) are written under gitignored `.temp/`, while
root `harness-adapter` manifests (`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`, `.mcp.json`, `mcp.json`,
and `harness-adapters/hermes/`) are tracked in the repository.

## Verification

```text
python -m mypy --strict src
python -m ruff check .
python -m pytest test/unit test/use_case
python scripts/assemble.py write
python scripts/assemble.py check
python scripts/validate.py
```

Canonical procedures and templates live under [skills/](skills/).

## License

Licensed under the [Apache License 2.0](LICENSE). Release history is tracked in [CHANGELOG.md](CHANGELOG.md).
