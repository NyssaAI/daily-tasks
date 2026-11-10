# Plugin Architectural Review & Refinement Plan: `daily-tasks`

> [!IMPORTANT] Scope Directive
> This document records the architectural evaluation and refinement plan for `daily-tasks`. It identifies compliance, risks, and concrete remediation steps across the canonical plugin authoring standards.

**Evaluation Date**: `2026-11-10`  
**Evaluator**: `plugin-builder`  
**Current Version**: `0.10.0`  
**Plugin Archetype**: `Hybrid Code`  
**Current Architectural Style**: `Encapsulated Facade`  

---

## Executive Summary

`daily-tasks` (`v0.10.0`) is a well-engineered Hybrid Code agent plugin implementing personal task management, local-day planning, and anytime check-in reconciliation over editable Markdown records and a Python MCP server (`daily-tasks-mcp`). Its prompt architecture cleanly embodies the **Encapsulated Facade** topology: a lean 54-line router (`skills/daily-tasks/SKILL.md`) dispatches across five internal workflows (`setup.md`, `capture.md`, `records.md`, `plan.md`, `checkin.md`) backed by eight domain references (`references/*.md`) and six templates (`assets/*.md`). Context economics, scope directives, trigger frontmatter precision, cognitive mode formatting, and the deterministic MCP/CST write boundary are all exemplary, with 334 passing Python unit and MCP session tests and zero drift across `1254` assembled artifact files.

Despite strong skill authoring and core Python design, one remaining area requires targeted work to reach full cross-plugin release certification:
1. **Repository Layout & Canonical Directories (Dimension 2 — Resolved / Compliant)**: `.nyssa-ai/` is now gitignored in `.gitignore` and untracked from the repository index (`plugin-builder/scripts/validate.py` passes with `passed: true` and `0` findings), Hermes runtime registration is sourced from canonical `adapters/hermes/__init__.py`, Hybrid Code use-case integration tests reside in `test/use_case/`, and `test/unit/test_package.py` verifies `scripts/assemble.py` and `scripts/validate.py`.
2. **Package Organization & Manifest Conformance (Dimension 4 — Resolved / Compliant)**: Root `.mcp.json` (`uv run --directory ${CLAUDE_PLUGIN_ROOT} daily-tasks-mcp`), assembled portable/Hermes `mcp.json`, and Antigravity `mcp_config.json` now provide self-contained bundle-anchored stdio MCP definitions, and `README.md` includes `Version **0.10.0**` parity and accurate dot-directory tracking guidance.
3. **Evaluation Matrix, Behavioral Coverage & Receipt Automation (Dimension 10 — Non-Compliant)**: While `evals/waza/skills/daily-tasks/` provides 10 strong positive triggers, 7 near-neighbor negative triggers, and 1 programmatic behavioral setup test (`personal-only.yaml`), 28 of 29 setup catalog scenarios remain unimplemented, workflows `capture`, `records`, `plan`, and `checkin` have zero behavioral eval tasks, and the `evals/` tree lacks `matrix.json`, `evals/report.py` (`generate`/`check`/`release`), `evals/results/` or `evals/evidence/results/` run bundles, and `evals/reports/` scorecards (`LATEST.md` is hand-authored and cites stale `2026-11-04` / `1234`-file counts).

---

## Dimension-by-Dimension Findings

### 1. Topology & Architectural Style
- **Status**: `Compliant`
- **Observed Style**: `Encapsulated Facade`
- **Analysis**:
  - Global system prompt footprint: Minimal and optimal. Only the single router skill `skills/daily-tasks/SKILL.md` (54 lines; single-paragraph frontmatter description) is exposed to the global skill catalog in `plugin.json` and assembled bundles. All 5 sub-workflows (`workflows/*.md`) omit YAML trigger frontmatter so they load strictly on demand after router triage.
  - Trigger collision & surface clutter: Zero internal leaf-skill collision within the repository source. The router triage table cleanly partitions `setup.md`, `capture.md`, `records.md`, `plan.md`, and `checkin.md` across a stateful shared data model (`profile.json`, canonical Markdown records, and the 3-screen MCP session). *(Operational note: if upgrading a host cache from an older pre-facade Public Suite release that exposed `daily-tasks-capture`, `daily-tasks-plan`, etc., ensure stale cached leaf folders are purged during installation so legacy skills do not shadow the facade.)*
- **Remediation Steps**:
  - [x] No structural topology changes required; retain the Encapsulated Facade architecture.

### 2. Repository Layout & Canonical Directories
- **Status**: `Compliant` *(Remediated 2026-11-10)*
- **Enumerated Directory & Test Inventory**:
  - **Observed Top-Level Directories**: `.claude-plugin/`, `.codegraph/`, `.codex-plugin/`, `.cursor-plugin/`, `.git/`, `.github/`, `.nyssa-ai/` (gitignored), `.obsidian/`, `.pytest_cache/`, `.temp/`, `.vscode/`, `.worktrees/`, `adapters/`, `artifacts/`, `docs/`, `evals/`, `scripts/`, `skills/`, `src/`, `test/`
  - **Unignored Non-Canonical Top-Level Directories**: `None` (`plugin-builder/scripts/validate.py` passes with `passed: true`, `findings: []`)
  - **Disguised Monorepo / Sub-Package Trees**: `None`
  - **Observed Immediate Subdirectories in `evals/`**: `waza/`
  - **Flat / Uncategorized Scenario Folders in `evals/` Root**: `0 (None)`
  - **Co-Mingled Test Files Outside `test/`**: `None` (all automated tests reside under `test/unit/` and `test/use_case/`)
- **Top-Level Directories Check**:
  - Single plugin root invariant (zero nested `plugins/` or disguised `standards/`/`packages/` monorepos): `Pass`
  - Canonical top-level directories present (`skills/`, `src/`, `test/`, `evals/`, `docs/`, `scripts/`, `adapters/`, `.temp/`): `Pass` (`test/unit/` and `test/use_case/` both present and passing)
  - Zero unignored extraneous top-level folders (workspace directories ignored by `.gitignore` such as `.worktrees/`, `.nyssa-ai/`, or `.obsidian/` are permitted): `Pass`
  - Zero loose scripts or non-canonical files in root: `Pass` (`.gitattributes`, `.gitignore`, `.mcp.json`, `AGENTS.md`, `CLAUDE.md`, `LICENSE`, `plugin.json`, `pyproject.toml`, `README.md`, `uv.lock`)
  - Prohibited locations clean (no scripts in `skills/`, no tests co-mingled in `scripts/` or domain folders): `Pass`
  - Clean `evals/` hierarchy (zero flat benchmark scenario dumps; grouped under `evals/scenarios/<group>/` or `evals/suites/`): `Pass`
- **Remediation Steps**:
  - [x] Gitignored `.nyssa-ai/` and removed its tracked entries from the Git index (`git rm -r --cached .nyssa-ai`), documenting the intentional `REPO-GITIGNORE` exception for strict plugin-root conformance.
  - [x] Created `test/use_case/daily_tasks/` for Hybrid Code end-to-end operational MCP session tests (`test_full_planning_session.py`).
  - [x] Added `test/unit/test_package.py` exercising `scripts/assemble.py` and `scripts/validate.py`.
  - [x] Extracted Hermes registration Python code into canonical `adapters/hermes/__init__.py`.

### 3. Required Host Adapters
- **Status**: `Compliant`
- **Host Adapters Check**:
  - Host adapters directly at repository root: `Pass`
  - Claude adapter present and valid (`.claude-plugin/plugin.json`): `Pass`
  - Codex adapter present and valid (`.codex-plugin/plugin.json`): `Pass`
  - Cursor adapter present and valid (`.cursor-plugin/plugin.json`): `Pass`
  - Host adapters cleanly generated/assembled from canonical root source, not hand-edited or nested: `Pass` (`python scripts/assemble.py check` verified `1255` generated files match canonical source across root adapters and `artifacts/{portable,antigravity,cowork,hermes}`)
- **Remediation Steps**:
  - [x] Required root host adapters exist, match `plugin.json` (`0.10.0`), and pass deterministic `assemble.py check`.

### 4. Package Organization & Manifest Conformance
- **Status**: `Compliant` *(Remediated 2026-11-10)*
- **Manifest Checks**:
  - Root `plugin.json` schema conformance and identity: `Pass` (`daily-tasks` `0.10.0`, matches `pyproject.toml`, `README.md`, and host manifests)
  - Release artifact hygiene (zero leaks of `evals/`, `docs/`, `.temp/`, `.nyssa-ai/` into bundles): `Pass` (`scripts/assemble.py` packages only `plugin.json`, host-appropriate MCP declarations, `LICENSE`, `pyproject.toml`, `skills/`, and `src/` with `_EXCLUDED_DIRS` filtering)
- **Remediation Steps**:
  - [x] Updated `.mcp.json` (`uv run --directory ${CLAUDE_PLUGIN_ROOT} daily-tasks-mcp`) and generated host-specific `mcp.json` (`portable`, `hermes`) and `mcp_config.json` (`antigravity`) in `scripts/assemble.py` so bundled MCP servers launch directly from the plugin bundle without requiring a pre-installed global `PATH` binary.
  - [x] Moved Hermes registration code from `scripts/assemble.py` into `adapters/hermes/__init__.py` and verified assembly from canonical source.
  - [x] Updated `README.md` with `Version **0.10.0**` parity (enforced in `scripts/validate.py`) and accurate dot-directory tracking documentation.

### 5. Single Responsibility & Scope Directives
- **Status**: `Compliant`
- **Scope Directives Check**:
  - Top-of-file Scope Directives in all rules (`rules/*.md`): `Present (N/A — no rules/*.md files)`
  - Top-of-file Scope Directives in all workflows (`workflows/*.md`): `Present` (verified in all 5 workflows: `capture.md`, `checkin.md`, `plan.md`, `records.md`, `setup.md`)
  - Top-of-file Scope Directives in references (`references/*.md`): `Present` (verified in all 8 references: `cli.md`, `operations.md`, `planning-flow.md`, `records.md`, `response-conventions.md`, `template-updates.md`, `templates.md`, `verification.md`)
- **Responsibility Overlap**:
  - Clean separation of concerns across all 13 scoped files. Every workflow owns procedural gates and execution steps while delegating schema, protocol, and domain rationale to `references/*.md` via relative links (`#anchor` targets all verified).
  - Minor schema cross-reference leak: `skills/daily-tasks/workflows/plan.md` (lines 27, 42) and `skills/daily-tasks/references/cli.md` (lines 47, 64) mention `docs/specs/message.json`, `docs/specs/operations.json`, and `docs/specs/decision-log-entry.json` in plain text. Because `docs/` is excluded from assembled release artifacts (`artifacts/*`), installed agents cannot read `docs/specs/*.json` at runtime. While `plan.md` and `cli.md` summarize the fields inline, moving or mirroring normative runtime JSON schemas into `skills/daily-tasks/assets/` (or `references/`) makes packaged bundles 100% self-contained.
- **Remediation Steps**:
  - [ ] Replace plain-text `docs/specs/*.json` references inside `skills/daily-tasks/` (and `src/daily_tasks/server/tool_definitions.py` descriptions) with self-contained schema definitions in `skills/daily-tasks/assets/` or inline `inputSchema` properties so packaged artifacts never reference unbundled `docs/specs/` paths.

### 6. Context Economics & Progressive Disclosure
- **Status**: `Compliant`
- **Metrics**:
  - `SKILL.md` line count: `54` lines (Limit: <500 lines — well within budget)
  - Workflow line counts: `setup.md` (`110`), `records.md` (`74`), `plan.md` (`60`), `capture.md` (`54`), `checkin.md` (`52`)
  - Reference line counts: `planning-flow.md` (`97`), `cli.md` (`80`), `records.md` (`72`), `response-conventions.md` (`55`), `templates.md` (`43`), `verification.md` (`36`), `template-updates.md` (`35`), `operations.md` (`30`)
  - Bulky domain schemas/tables offloaded to `references/` and `assets/`: `Yes`
  - Exclusion of general programming knowledge: `Yes`
- **Remediation Steps**:
  - [x] Context economics and progressive disclosure are tightly optimized; no file exceeds 110 lines.

### 7. Trigger Precision & Frontmatter Design
- **Status**: `Compliant`
- **Frontmatter Checks**:
  - Third-person imperative phrasing (`"Use this skill when..."`): `Pass` (`Use this skill when the user asks to "set up Daily Tasks"...`)
  - Quoted realistic user trigger phrases: `Pass` (`"set up Daily Tasks"`, `"capture possible tasks from notes"`, `"create or update a project, milestone, or task"`, `"fix malformed record files"`, `"plan my day"`, `"check in and reconcile edits"`)
  - Explicit negative boundary conditions: `Present` (`Do NOT use this skill for calendar time-blocking or scheduling work into available time slots.`)
- **Analysis**:
  - Frontmatter cleanly triggers across all five encapsulated capabilities. As a minor hardening improvement, the negative boundary could also name near-neighbor sibling plugins tested in Waza (`para-vault` for reference note filing, `manage-file-operations` for raw folder moves, and `plan-product` for product roadmaps) to match the exact boundary precision of those peer skills.
- **Remediation Steps**:
  - [ ] *(Optional polish)* Expand the `Do NOT use this skill for...` clause in `skills/daily-tasks/SKILL.md` to explicitly exclude PARA reference-note filing (`para-vault`), raw directory moves (`manage-file-operations`), and product feature roadmapping (`plan-product`).

### 8. Deterministic Boundary
- **Status**: `Compliant`
- **Boundary Checks**:
  - Qualitative reasoning in markdown vs. code in `src/` for computation/parsing: `Compliant` (StateGraph construction, message window filtering, suggestion pre-matching, row-handle mapping, surgical CST Markdown editing, atomic writes, secret loopback capture, and append-only decision logging all live in `src/daily_tasks/` behind strict Pydantic models and `mypy --strict`)
  - Observable verification checklist in procedure instructions: `Present` (`SKILL.md` and all 5 `workflows/*.md` conclude with explicit `## Verification` checklists)
  - Parameter sanitization and actionable error diagnostics: `Compliant` (`additionalProperties: False` on all 8 MCP tool input schemas; path traversal `..` rejection; malformed file isolation in `payload.malformed_files`; strict `stderr`-only logging keeping `stdout` pure for JSON-RPC 2.0)
- **Analysis**:
  - One subtle contract detail in `src/daily_tasks/server/tool_definitions.py` (`operations` and `messages` array items use `{"type": "object"}` with `"Operations as in docs/specs/operations.json"` rather than full JSON Schema object properties). Publishing explicit JSON Schema item properties in `TOOL_DEFINITIONS` will improve first-try tool call accuracy in hosts without access to `docs/specs/`.
- **Remediation Steps**:
  - [ ] Inline full JSON Schema item definitions for `messages` and `operations` in `src/daily_tasks/server/tool_definitions.py` instead of deferring to `docs/specs/*.json` in description text.

### 9. Cognitive Mode Formatting & Authoring Style (Prose vs. Checklists)
- **Status**: `Compliant`
- **Format vs. Cognitive Mode Checks**:
  - Subagent instructions (`agents/*.md` e.g. `adversary.md`, `eval.md`) use structured checklists and bulleted directives: `Compliant (N/A — Facade topology uses no subagents)`
  - Rules (`rules/*.md`) and execution gates use bulleted directives without narrative sprawl: `Compliant` (router and workflow gates use crisp numbered/bulleted directives)
  - Skills and runbooks (`SKILL.md`, `workflows/*.md`) use procedural checklists and clear gates: `Compliant`
  - References (`references/*.md`) reserve narrative prose for architectural theory, context, and domain philosophy: `Compliant` (`operations.md`, `planning-flow.md`, `records.md`, `response-conventions.md`, `template-updates.md`, `templates.md`, and `verification.md` use cohesive prose paragraphs paired with concise lookup tables where appropriate)
- **Remediation Steps**:
  - [x] Formatting aligns cleanly with cognitive mode best practices across all skill and reference files.

### 10. Evaluation Suite Quality & Rigor
- **Status**: `Non-Compliant`
- **Trigger Quality & Coverage**:
  - Positive triggers: `10` realistic, distinct user prompts covering router, setup (4 variants), capture, records (creation + malformed repair), plan, and check-in (Target: 3–5): `Pass`
  - Negative boundaries: `7` challenging near-neighbor prompts testing calendar time-blocking, `para-vault`, `ce-babysit-pr`, `plan-product`/Pomodoro, `manage-file-operations`, `write-like-me`, and cross-timezone calendar invites (Target: 3–5): `Pass`
  - Avoidance of trivial negatives: `Pass`
- **Grader & Assertion Depth**:
  - Meaningful assertions (structural contracts, artifacts, exact phrases): `Needs More` — `personal-only.yaml` + `graders/validate-personal-only.py` is rigorous (verifies `schema_version: 2`, exact JSON keys, absence of workspace artifacts, skill invocation, and response regexes), **but** 28 of 29 scenarios in `scenario-catalog.yaml` have no executable task/grader, and `capture`, `records`, `plan` (MCP 3-screen flow), and `checkin` have **zero** behavioral evaluation suites.
- **Matrix & Verification Receipts**:
  - Cross-host matrix declared (`evals/matrix.json`): `Missing`
  - Automated report generator & non-mutating check (`evals/report.py` + `evals/reports/`): `Missing`
  - Verified evidence bundles (`evals/results/` or `evals/evidence/results/`): `Missing` (no `metadata.json` or host trace receipts exist)
  - Release receipts verified and fresh (`evals/LATEST.md`): `Stale` (`evals/LATEST.md` is hand-edited rather than generated from machine evidence, dated `2026-11-04`, cites `1234` generated files instead of current `1254`, cites `330` unit tests instead of current `334`, and has uncommitted source modifications in the working tree)
- **Remediation Steps**:
  - [ ] Add `evals/matrix.json` and `evals/report.py` (`generate`, `check`, `release`, `summary`) so `evals/LATEST.md` and `evals/reports/yyyy.mm.dd-eval-results.md` are deterministically generated and validated against `candidate_sha256` and `evals/evidence/results/` (or `evals/results/`).
  - [ ] Expand executable behavioral scenarios under `evals/scenarios/` (or `evals/waza/skills/daily-tasks/tasks/behavior/`) with deterministic Python graders covering workspace setup, candidate capture acceptance gates, malformed record surgical repair, 3-screen MCP daily planning (`payload.screen` fidelity + saved `YYYY.MM.DD-daily-plan.md`), and check-in conflict reconciliation.
  - [ ] Execute live host matrix runs across claimed targets (Claude Code, Claude Cowork, Codex, Cursor, Antigravity, Hermes Agent, OpenClaw) and commit verified `results/` / `attempts/` receipts before claiming native host release readiness.

---

## Prioritized Remediation Roadmap

1. **Phase 1: Completed (Structural Layout & Packaging — Dimensions 2 & 4)**
   - [x] Gitignored `.nyssa-ai/` so `python <plugin-builder>/scripts/validate.py .` passes with zero findings (`passed: true`).
   - [x] Added `test/use_case/daily_tasks/` for Hybrid Code operational integration tests and `test/unit/test_package.py` for `scripts/assemble.py` and `scripts/validate.py`.
   - [x] Extracted inline Hermes Python adapter code from `scripts/assemble.py` into `adapters/hermes/__init__.py`.
   - [x] Made `.mcp.json`, portable/Hermes `mcp.json`, and Antigravity `mcp_config.json` self-contained relative to the installed plugin root, and updated `README.md` version parity (`Version **0.10.0**`) and dot-directory guidance.
2. **Phase 2: Medium Priority (Optional Schema Inlining Polish)**
   - [ ] Inline `messages` and `operations` JSON Schema item definitions in `src/daily_tasks/server/tool_definitions.py` and bundle any referenced spec contracts under `skills/daily-tasks/assets/` so runtime skills and MCP tools never cite unshipped `docs/specs/*.json` paths.
3. **Phase 3: Verification & Packaging (Evals Matrix, Behavioral Suites & Receipts — Dimension 10)**
   - [ ] Implement `evals/matrix.json` and `evals/report.py` (`generate` / `check` / `release`) and establish `evals/evidence/{results,attempts}/` + `evals/reports/`.
   - [ ] Build multi-workflow behavioral eval fixtures and programmatic graders covering `capture`, `records`, `plan` (MCP 3-screen session), `checkin`, and priority `scenario-catalog.yaml` cases.
   - [ ] Re-run `python scripts/assemble.py write`, `python scripts/assemble.py check`, `python scripts/validate.py`, `python <plugin-builder>/scripts/validate.py .`, and `python evals/report.py check` to refresh `evals/LATEST.md` with current receipts.
