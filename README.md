# Daily Tasks

Version **0.11.1**

Personal task management and daily planning through an encapsulated `daily-tasks` agent skill,
five focused workflows, and a deterministic Python Model Context Protocol (MCP) planning server.
Maintain projects, milestones, tasks and external blockers in editable Markdown; review your own
and delegated work in a local-day plan. The skill provides capabilities to your agent, without
becoming an autonomous assistant persona or fitting work into a timeframe.

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
| Setup | `skills/daily-tasks/workflows/setup.md` | Identity, timezone, priorities, storage scope and MCP connector setup |
| Capture | `skills/daily-tasks/workflows/capture.md` | Candidate review and explicit acceptance |
| Records | `skills/daily-tasks/workflows/records.md` | Accepted work, delegation, progress, DoD, blockers and malformed-file repair |
| Plan | `skills/daily-tasks/workflows/plan.md` | Daily selections, ownership review and explicit future planning |
| Check-in | `skills/daily-tasks/workflows/checkin.md` | Reconciliation, progress reports and resumable decisions |

## Storage and authority

- Preferences: version-2 layers at `<workspace root>/.nyssa-ai/daily-tasks/profile.json`
  and `~/.nyssa-ai/daily-tasks/profile.json`. Project leaves override user defaults;
  omission inherits and documented null leaves select packaged defaults. Reuse accepted
  explicit pointers. Portable `.` and `./...` paths resolve against the explicitly
  captured workspace binding; `~/...` resolves against the current host's home directory.
- Operating state: `<workspace root>/.nyssa-ai/daily-tasks/`, independent of shared
  preferences. Divergent stores require reconciliation. Reuse a verified established binding.
- Decision log: `<workspace root>/.nyssa-ai/daily-tasks/decision-log.json`, append-only
  logical history written by the planning session server upon explicit confirmation.
- Daily plans: `<workspace root>/2-areas/daily-plans/YYYY.MM.DD-daily-plan.md` (or
  `<workspace root>/daily-plans/YYYY.MM.DD-daily-plan.md`) by default.
- Project index plus `m1-name/m1-name.md` milestones and sibling `t1-name.md` tasks.
  Each milestone and task owns its own Definition of Done; tasks also own requirements.
  Flat milestone `inputs/` and `outputs/` hold files linked by tasks. Navigation follows
  `project -> milestone -> task -> files`. Project-wide blockers stay in `blockers/`.
  All local work stays in the project, including `.temp/` scratch.
- UUIDv7 document IDs use frontmatter `id`.
  DoD criterion IDs and projection `ref` IDs use hidden comments. Wiki links use readable labels.
- Store GMT, present configured local time with timezone. Human email owner; optional
  person/agent assignee, falling back to owner. Target dates are optional and explicit.

## Runtime and packaging

Python 3.12 or later (managed with `uv` via `pyproject.toml`) runs the deterministic
MCP planning session server (`daily-tasks-mcp`). The planning server is accessed strictly
via host MCP tool calls (`daily_tasks_*`); agents never invoke it as a CLI command.
All diagnostic logging goes to `stderr` so `stdout` remains pure for MCP JSON-RPC 2.0 frames.

Daily Tasks enforces a mandatory full-setup gate: downstream workflows (`plan`, `records`, `checkin`,
and `capture`) never run unless `daily_tasks_*` MCP tools are live in the active harness, Schema
Version 2 `profile.json` bindings (`projectsRoot`, `dailyPlansRelative`, `user.email`, IANA `timezone`,
and `sources`) are present, and workspace templates are initialized. When any setup gate is incomplete
or uses a legacy `.nyssaai` v1 profile, the skill immediately halts downstream work and runs harness-aware
setup (`skills/daily-tasks/workflows/setup.md` and `skills/daily-tasks/references/harness-setup.md`).
Malformed files and unparseable records trigger surgical repairs (`skills/daily-tasks/workflows/records.md`).

```text
# Host registration / direct server launch:
uv run daily-tasks-mcp --workspace-root /absolute/workspace
uv run python -m daily_tasks.server --workspace-root /absolute/workspace
# Out-of-band secrets (masked prompt or loopback page; never pasted into chat):
uv run python -m daily_tasks.auth.secret gmail
uv run python -m daily_tasks.auth.secret vault --name bws --kind bitwarden-secrets --project-id ID
# Gmail OAuth setup:
uv run python -m daily_tasks.auth.gmail --config-dir /absolute/home/.nyssa-ai/daily-tasks
```

See [MCP & CLI contract](skills/daily-tasks/references/cli.md), [record conventions](skills/daily-tasks/references/records.md)
and [reconciliation](skills/daily-tasks/references/operations.md).

Install a host bundle from the [latest release](https://github.com/NyssaAI/daily-tasks/releases/latest),
or build from source with `python scripts/assemble.py write`. Generated artifact bundles (`artifacts/`)
and workspace tool dot-directories are not tracked in Git, while canonical root host harnesses
(`.claude-plugin/`, `.codex-plugin/`, `.cursor-plugin/`) are assembled from `plugin.json`; a source
checkout should run `python scripts/assemble.py write` before host installation. `artifacts/portable`
contains the portable/Codex/Claude/Cursor bundle, `artifacts/cowork` contains the Cowork bundle, and
`artifacts/antigravity` and `artifacts/hermes` provide host-specific manifests and MCP configurations.

## Verification

```text
python -m mypy --strict src
python -m ruff check .
python -m pytest test/unit test/use_case
python scripts/assemble.py write
python scripts/assemble.py check
python scripts/validate.py
```

Contributors with the `dev-standards` plugin installed can sync and run the local structural standards suite via `python <dev-standards-plugin>/src/python/check_adoption.py . --sync` followed by `python .nyssa-ai/dev-standards/python/scripts/check_adoption.py . --run` (`.nyssa-ai/` remains gitignored to preserve clean plugin packaging).

Canonical procedures and templates live under [skills/](skills/).
