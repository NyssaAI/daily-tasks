# Changelog

## Unreleased

## 0.11.3 - Cross-plugin 11-host adapters, CI & Waza parity, config.json & runtime_root, Apache-2.0, routing, and validator parity

- Expanded `scripts/validate.py` and `test/unit/test_package.py` to enforce full cross-plugin `plugin-builder` validator parity: self-loaded root and top-level layout lockdown, `.gitattributes` LF rules, `docs/` Allowed-Set and `codegraph.db` / `.gitignore` invariants with code-span-stripped Markdown link validation, `test/` isolation, skill BOM/description/`Scope Directive`/`## Verification` and retired `openai.yaml` checks, retired runtime token bans, and `evals/` directory and 11-host `matrix.json` version parity.
- Added a facade `> [!IMPORTANT] Scope Directive` and reciprocal cross-plugin routing boundaries (`para-vault`, `manage-file-operations`, and `write-like-me` in `agent-skills`) across `skills/daily-tasks/SKILL.md`, `skills/daily-tasks/workflows/capture.md`, and `skills/daily-tasks/workflows/records.md`.
- Aligned 11-host `harness-adapter` distribution parity across `.claude-plugin/plugin.json`, `.codex-plugin/plugin.json`, `.cursor-plugin/plugin.json`, `.tessl-plugin/plugin.json`, `gemini-extension.json`, `.mcp.json`, Agent Plugins v1 `mcp.json`, Antigravity `mcp_config.json` bootstrapper, and Hermes `harness-adapters/hermes/plugin.py` (assembled to `__init__.py` in `.temp/dist/hermes`).
- Added cross-platform CI verification (`.github/workflows/validate.yml` on `ubuntu-latest` and `windows-latest`, including `tzdata` for Windows IANA timezone resolution) and deterministic evaluation reporting (`evals/report.py` and 11-row `evals/matrix.json` anchoring `evals/LATEST.md` to `candidate_sha256()`).
- Calibrated the Waza evaluation suite (`evals/waza/skills/daily-tasks/eval.yaml` with `18/18` positive/negative trigger tasks and `behavior.yaml` behavioral preflight manifest) with structural validation in `scripts/validate.py`.
- Migrated configuration resolution to `NyssaAI.Configuration` conventions (`~/.nyssa-ai/daily-tasks/config.json` -> `<repo_root>/.nyssa-ai/daily-tasks/config.json` with read-only legacy `profile.json` fallback and zero `.nyssa-ai/` writes in `vault_root`), enforced the 4-step `runtime_root` resolution chain (`--runtime-root` -> `NYSSA_RUNTIME_ROOT` -> agent persona `cwd` with `SOUL.md` + `IDENTITY.md` -> configured/default `runtime/`), and added opt-in usage telemetry (`usage/events.jsonl`).
- Migrated the repository, `plugin.json`, `pyproject.toml`, and assembled host manifests to the canonical NyssaAI `Apache-2.0` license and added tracked `CHANGELOG.md`.

## 0.11.2 - Cross-plugin Ubiquitous Language, `vault_root`/`runtime_root` separation, and Scale B modular monolith

- Aligned Ubiquitous Language across `docs/GLOSSARY.md`, `docs/concepts/`, `docs/features/`, `AGENTS.md`, and `skills/daily-tasks/`, separating `vault_root` editable Markdown records from `runtime_root` mutable operational state and staging assembled distributions strictly under `.temp/dist/`.
- Restructured `src/daily_tasks/` as a Scale B SOLID Modular Monolith (`core/`, `records/`, `communications/`, `transports/mcp/`, and `hosting/`) with committed `docs/code-map/codegraph.db` snapshot parity.

## 0.11.1 - Isolated MCP `uv` runtime environment and Hermes setup alignment

- Isolated `launch_mcp.py` `uv` virtual environment and cache directories outside read-only installed plugin directories and aligned Hermes setup documentation and unit tests.

## 0.11.0 - Harness-aware full-setup gate, portable MCP launcher, and Agent Plugins v1 `mcp.json`

- Enforced a mandatory full-setup gate across downstream workflows (`plan`, `records`, `checkin`, `capture`) with deterministic MCP setup tools (`daily_tasks_setup_status`, `daily_tasks_configure_vault`, `daily_tasks_capture_secret`) and harness-aware setup guidance (`skills/daily-tasks/references/harness-setup.md`).
- Added portable `src/daily_tasks/launch_mcp.py`, headless `--redirect-port` support for interactive Gmail OAuth setup, and Agent Plugins v1 root `mcp.json` manifest generation.

## 0.10.1 - Zero-footprint `dev-standards` adoption and Python MCP server consolidation

- Removed checked-in `.nyssa-ai/dev-standards/` repository copies in favor of zero-footprint external `dev-standards` conformance.
- Consolidated the encapsulated `skills/daily-tasks/` facade (`setup`, `capture`, `records`, `plan`, `checkin` workflows) with the Python `daily-tasks-mcp` stdio server, Markdown CST surgical writer, 3-screen planning session state graph, out-of-band secret capture, pluggable secret vaults, and 7-day initial lookback connector ingestion (`0.10.0`–`0.10.1`).

## 0.9.3 - Plugin manifest version synchronization

- Bumped `plugin.json` release metadata to `0.9.3` for downstream marketplace synchronization.

## 0.9.2 - Automated marketplace release dispatch

- Added `.github/workflows/release-marketplace.yml` to dispatch marketplace updates automatically on version tags and bumped `plugin.json` to `0.9.2`.

## 0.9.1 - Two-step pre-rendered planning drafts, cross-milestone pagination, and write-only decision log

- Accelerated daily planning session preparation (`<1s` startup benchmark) with 2-step pre-rendered planning drafts, cross-milestone task pagination, and append-only decision-log writes.

## 0.7.0 - Modern `src/` repository layout and subpath imports

- Reorganized runtime modules under `src/` with explicit subpath imports, updated harness smoke checks, and refreshed evaluation fixtures.

## 0.6.3 - Source-only repository packaging

- Removed checked-in `artifacts/` build copies in favor of source-only repository tracking and deterministic `scripts/assemble.py` bundle generation.

## 0.6.2 - Vault-scoped planning recovery and layered configuration preservation

- Preserved layered user/workspace configuration and explicit vault state bindings during project index prewarming, template upgrades, and multi-date selection recovery (`0.3.6`–`0.6.2`).

## 0.3.5 - User and project configuration scopes

- Added layered user-scope and project-scope configuration resolution for Daily Tasks workspace bindings.

## 0.3.4 - Verified planning and record workflow guardrails

- Hardened explicit task acceptance, conflict-halted planning writes, Definition of Done retirement ordering, blocker naming, and runtime effect verification (`0.3.3`–`0.3.4`).

## 0.3.2 - Numbered milestone workspaces and daily plan templates

- Introduced explicit-acceptance Daily Tasks workflows, numbered milestone workspace directories, and Markdown daily plan templates (`0.3.1`–`0.3.2`).
