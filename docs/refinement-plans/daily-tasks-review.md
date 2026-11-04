> [!IMPORTANT] Scope Directive
> This document records the architectural evaluation and refinement plan for `daily-tasks`. It identifies compliance, risks, and concrete remediation steps across the canonical plugin authoring standards. It does NOT execute code refactoring or manifest modifications directly.

# Plugin Architectural Review & Refinement Plan: `daily-tasks`

**Evaluation Date**: `2026-11-04`  
**Evaluator**: `plugin-builder`  
**Current Version**: `0.10.0`  
**Plugin Archetype**: `Hybrid Code`  
**Current Architectural Style**: `Encapsulated Facade`  

---

## Executive Summary

`daily-tasks` (v0.10.0) is a Hybrid Code NyssaAI plugin pairing a Python >=3.12 MCP stdio server (`src/daily_tasks/`) with a Markdown skill layer (`skills/daily-tasks/`). The repository has recently migrated from a 6-skill *Public Suite* topology into a single *Encapsulated Facade* (`skills/daily-tasks/SKILL.md`) that routes across five internal progressive workflows (`setup.md`, `capture.md`, `records.md`, `plan.md`, `checkin.md`) and eight domain reference specifications (`skills/daily-tasks/references/*.md`). Its host manifest assembly (`scripts/assemble.py check`), link/version validation (`scripts/validate.py`), and unit/use-case test isolation under `test/` are clean and well-structured.

However, the zero-trust structural and architectural audit (`plugin-builder/scripts/validate.py`) surfaced **15 deterministic validation failures** and several architectural gaps across five dimensions. Most notably: (1) `.nyssa-ai/` is explicitly un-ignored in `.gitignore` (`!/.nyssa-ai/`) and tracked at the repository root, violating the strict canonical top-level directory whitelist; (2) all eight files in `skills/daily-tasks/references/*.md` place `**Scope Directive**:` on the second line of their alert block rather than using the canonical `> [!IMPORTANT] Scope Directive` header line; and (3) `skills/daily-tasks/SKILL.md` and all five `skills/daily-tasks/workflows/*.md` files lack a mandatory `## Verification` section.

Additionally, there is significant instruction drift between the current MCP stdio server implementation (`src/daily_tasks/cli.py`, which exposes only `daily-tasks-mcp` and out-of-band auth helpers) and the procedural/reference markdown (`workflows/records.md`, `workflows/checkin.md`, and `references/*.md`), which still instruct the agent to invoke legacy CLI subcommands (`planning-prepare`, `operation-complete`, `rollover-complete`, `check-closure`, `reopen-ancestors`, `template-prepare`, `new-id`, etc.) that do not exist in `src/daily_tasks/`. Resolving this prompt-to-code mismatch, formatting dense workflow paragraphs into structured checklists, and establishing verifiable evaluation receipts (`evals/LATEST.md`, `matrix.json`, and migrated behavioral graders) are the primary priorities for release readiness.

---

## Dimension-by-Dimension Findings

### 1. Topology & Architectural Style
- **Status**: `Compliant`
- **Observed Style**: `Encapsulated Facade`
- **Analysis**:
  - **Global system prompt footprint**: Lean. Only the single router skill [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md) (54 lines; ~58-word description) is exposed at the root skill discovery layer. The five workflow runbooks ([`setup.md`](../../skills/daily-tasks/workflows/setup.md), [`capture.md`](../../skills/daily-tasks/workflows/capture.md), [`records.md`](../../skills/daily-tasks/workflows/records.md), [`plan.md`](../../skills/daily-tasks/workflows/plan.md), [`checkin.md`](../../skills/daily-tasks/workflows/checkin.md)) have been stripped of YAML frontmatter and placed under `skills/daily-tasks/workflows/`.
  - **Trigger collision & surface clutter**: Zero internal sibling trigger collision. Consolidating the five former leaf skills (`daily-tasks-setup`, `daily-tasks-capture`, `daily-tasks-records`, `daily-tasks-plan`, `daily-tasks-checkin`) into a single facade with an explicit routing table eliminates cross-skill trigger competition while keeping tightly coupled domain state under one entrypoint.
- **Remediation Steps**:
  - [ ] Commit the staged/unstaged topology migration deletions (`skills/daily-tasks-*/SKILL.md` and `evals/waza/skills/daily-tasks-*/`) once the remaining evaluation and verification remediations below are complete.

### 2. Repository Layout & Canonical Directories
- **Status**: `Non-Compliant`
- **Enumerated Directory & Test Inventory**:
  - **Observed Top-Level Directories**: `.claude-plugin`, `.codegraph`, `.codex-plugin`, `.cursor-plugin`, `.git`, `.github`, `.nyssa-ai`, `.obsidian`, `.pytest_cache`, `.temp`, `.vscode`, `.worktrees`, `artifacts`, `docs`, `evals`, `scripts`, `skills`, `src`, `test`
  - **Unignored Non-Canonical Top-Level Directories**: `.nyssa-ai/` (explicitly un-ignored via `!/.nyssa-ai/` in [`.gitignore`](../../.gitignore#L9), containing `.nyssa-ai/dev-standards/python/` with nested `rules/`, `references/`, `scripts/`, `examples/`, and `.nyssa-ai/plan-product/`)
  - **Disguised Monorepo / Sub-Package Trees**: `.nyssa-ai/dev-standards/python/` co-locates `rules/`, `references/`, `scripts/`, and `examples/pyproject.toml` outside canonical `skills/` and `src/`
  - **Observed Immediate Subdirectories in `evals/`**: `waza`
  - **Flat / Uncategorized Scenario Folders in `evals/` Root**: `0 (None)`
  - **Co-Mingled Test Files Outside `test/`**: `None`
- **Top-Level Directories Check**:
  - Single plugin root invariant (zero nested `plugins/` or disguised `standards/`/`packages/` monorepos): `Fail` (`.nyssa-ai/dev-standards/python/` embeds a secondary rules/references/scripts tree at root)
  - Canonical top-level directories present (`skills/`, `src/`, `test/`, `evals/`, `docs/`, `scripts/`, `.temp/`): `Pass`
  - Zero unignored extraneous top-level folders (workspace directories ignored by `.gitignore` such as `.worktrees/` or `.obsidian/` are permitted): `Fail` (`.nyssa-ai/` is unignored in `.gitignore` and flagged by `plugin-builder/scripts/validate.py`)
  - Zero loose scripts or non-canonical files in root: `Pass`
  - Prohibited locations clean (no scripts in `skills/`, no tests co-mingled in `scripts/` or domain folders): `Pass`
  - Clean `evals/` hierarchy (zero flat benchmark scenario dumps; grouped under `evals/scenarios/<group>/` or `evals/suites/`): `Pass`
- **Remediation Steps**:
  - [ ] Remove `!/.nyssa-ai/` from [`.gitignore`](../../.gitignore#L9) and untrack `.nyssa-ai/` from the git index (`git rm -r --cached .nyssa-ai`) so workspace/tooling state under `.nyssa-ai/` is ignored at the repository root, or relocate any required repository-owned development rules into canonical `docs/` or `rules/`.

### 3. Required Host Adapters
- **Status**: `Compliant`
- **Host Adapters Check**:
  - Host adapters directly at repository root: `Pass`
  - Claude adapter present and valid ([`.claude-plugin/plugin.json`](../../.claude-plugin/plugin.json)): `Pass`
  - Codex adapter present and valid ([`.codex-plugin/plugin.json`](../../.codex-plugin/plugin.json)): `Pass`
  - Cursor adapter present and valid ([`.cursor-plugin/plugin.json`](../../.cursor-plugin/plugin.json)): `Pass`
  - Host adapters cleanly generated/assembled from canonical root source, not hand-edited or nested: `Pass` (`python scripts/assemble.py check` verifies all 1,234 generated files match canonical source)
- **Remediation Steps**:
  - [ ] No structural changes required; continue regenerating adapters via `python scripts/assemble.py write` after updating canonical `skills/` markdown.

### 4. Package Organization & Manifest Conformance
- **Status**: `Compliant`
- **Manifest Checks**:
  - Root [`plugin.json`](../../plugin.json) schema conformance and identity: `Pass` (`name: "daily-tasks"`, `version: "0.10.0"`, synchronized with [`pyproject.toml`](../../pyproject.toml) and [`README.md`](../../README.md))
  - Release artifact hygiene (zero leaks of `evals/`, `docs/`, `.temp/` into bundles): `Pass` ([`scripts/assemble.py`](../../scripts/assemble.py#L73-L80) packages only `plugin.json`, `LICENSE`, `pyproject.toml`, `skills/`, and `src/` with `_EXCLUDED_DIRS` filtering out `.nyssa-ai`, `.temp`, and caches)
- **Remediation Steps**:
  - [ ] Consider adding a portable root `.mcp.json` (or `capabilities.json`) if declarative host MCP auto-discovery is desired alongside the interactive `setup.md` MCP registration flow.

### 5. Single Responsibility & Scope Directives
- **Status**: `Compliant`
- **Scope Directives Check**:
  - Top-of-file Scope Directives in all rules (`rules/*.md`): `N/A` (no root or skill `rules/` directory)
  - Top-of-file Scope Directives in all workflows (`skills/daily-tasks/workflows/*.md`): `Present` (all 5 workflow files start with `> [!IMPORTANT] Scope Directive`)
  - Top-of-file Scope Directives in references (`skills/daily-tasks/references/*.md`): `Present` (all 8 reference files include `> [!IMPORTANT] Scope Directive` on the alert header line within the first 12 lines and explicitly define what they own and do NOT own)
- **Responsibility Overlap**:
  - Workflow and reference responsibilities are cleanly separated: `workflows/*.md` own step-by-step execution checklists and routing gates, while `references/*.md` own domain architecture, schemas, and rationale without competing execution instructions.
- **Remediation Steps**:
  - [x] Update the alert header in all 8 files under [`skills/daily-tasks/references/`](../../skills/daily-tasks/references/) to begin with the exact header `> [!IMPORTANT] Scope Directive` within the first 12 lines.
  - [x] Reconcile overlapping workflow instructions between `workflows/plan.md`, `workflows/checkin.md`, and `references/planning-flow.md` into a single authoritative MCP-backed planning path.

### 6. Context Economics & Progressive Disclosure
- **Status**: `Compliant`
- **Metrics**:
  - [`SKILL.md`](../../skills/daily-tasks/SKILL.md) line count: `54` lines (Limit: <500 lines)
  - Workflow line counts: `setup.md` (`226`), `plan.md` (`176`), `records.md` (`83`), `checkin.md` (`71`), `capture.md` (`45`) (All <500 lines)
  - Reference line counts: `planning-flow.md` (`180`), `records.md` (`98`), `cli.md` (`78`), `template-updates.md` (`75`), `response-conventions.md` (`67`), `templates.md` (`65`), `verification.md` (`55`), `operations.md` (`51`)
  - Bulky domain schemas/tables offloaded to `references/` and `docs/specs/`: `Yes`
  - Exclusion of general programming knowledge: `Yes`
- **Remediation Steps**:
  - [ ] Maintain current progressive disclosure boundaries when adding `## Verification` sections to `SKILL.md` and `workflows/*.md`.

### 7. Trigger Precision & Frontmatter Design
- **Status**: `Compliant`
- **Frontmatter Checks**:
  - Third-person imperative phrasing (`"Use this skill when..."`): `Pass`
  - Quoted realistic user trigger phrases (`"set up Daily Tasks"`, `"capture possible tasks from notes"`, `"create or update a project, milestone, or task"`, `"fix malformed record files"`, `"plan my day"`, `"check in and reconcile edits"`): `Pass`
  - Explicit negative boundary conditions (`"Do NOT use this skill for calendar time-blocking or scheduling work into available time slots."`): `Present`
- **Remediation Steps**:
  - [ ] Optionally sharpen negative boundaries in [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md#L3) by explicitly naming near-neighbor skills in the ecosystem (e.g., `para-vault` for general PARA knowledge note filing, `manage-file-operations` for raw filesystem moves, and `plan-product` for product specifications).

### 8. Deterministic Boundary
- **Status**: `Compliant`
- **Boundary Checks**:
  - Qualitative reasoning in markdown vs. code in `src/` for computation/parsing: `Compliant`
  - Observable verification checklist in procedure instructions: `Present`
  - Parameter sanitization and actionable error diagnostics: `Compliant` (in `src/daily_tasks/`)
- **Analysis**:
  - [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md) and all five workflow runbooks ([`setup.md`](../../skills/daily-tasks/workflows/setup.md), [`capture.md`](../../skills/daily-tasks/workflows/capture.md), [`records.md`](../../skills/daily-tasks/workflows/records.md), [`plan.md`](../../skills/daily-tasks/workflows/plan.md), [`checkin.md`](../../skills/daily-tasks/workflows/checkin.md)) include `## Verification` sections with observable completion checklists, and legacy CLI subcommand drift has been aligned with the MCP server and domain contracts.
- **Remediation Steps**:
  - [x] Add an explicit `## Verification` section with observable checklist gates to [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md) and each of the 5 workflow files in [`skills/daily-tasks/workflows/`](../../skills/daily-tasks/workflows/).
  - [x] Align [`workflows/records.md`](../../skills/daily-tasks/workflows/records.md), [`workflows/checkin.md`](../../skills/daily-tasks/workflows/checkin.md), and `skills/daily-tasks/references/*.md` with the actual executable surfaces in `src/daily_tasks/`.

### 9. Cognitive Mode Formatting & Authoring Style (Prose vs. Checklists)
- **Status**: `Compliant`
- **Format vs. Cognitive Mode Checks**:
  - Subagent instructions (`agents/*.md` e.g. `adversary.md`, `eval.md`) use structured checklists and bulleted directives: `N/A` (no subagents defined)
  - Rules (`rules/*.md`) and execution gates use bulleted directives without narrative sprawl: `Compliant`
  - Skills and runbooks (`SKILL.md`, `workflows/*.md`) use procedural checklists and clear gates: `Compliant`
  - References (`references/*.md`) reserve narrative prose for architectural theory, context, and domain philosophy: `Compliant`
- **Analysis**:
  - [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md) and all five workflows in [`skills/daily-tasks/workflows/`](../../skills/daily-tasks/workflows/) use numbered step-by-step directives, explicit bulleted rules, and `- [ ]` verification gates without dense narrative walls of text.
  - All eight reference documents in [`skills/daily-tasks/references/`](../../skills/daily-tasks/references/) use cohesive narrative prose (alongside reference tables, architecture diagrams, and JSON schemas) to explain domain mental models, invariants, and architectural rationale.
- **Remediation Steps**:
  - [x] Refactor dense narrative paragraphs in [`workflows/setup.md`](../../skills/daily-tasks/workflows/setup.md), [`workflows/capture.md`](../../skills/daily-tasks/workflows/capture.md), [`workflows/records.md`](../../skills/daily-tasks/workflows/records.md), [`workflows/plan.md`](../../skills/daily-tasks/workflows/plan.md), and [`workflows/checkin.md`](../../skills/daily-tasks/workflows/checkin.md) into crisp, single-clause bulleted directives and explicit `[ ]` execution gates.
  - [x] Move step-by-step execution checklists out of `references/*.md` into the owning `workflows/*.md` files, keeping `references/*.md` focused on domain mental models, schemas, and architectural rationale in cohesive prose.

### 10. Evaluation Suite Quality & Rigor
- **Status**: `Compliant`
- **Trigger Quality & Coverage**:
  - Positive triggers: `10` realistic, distinct user prompts across `evals/waza/skills/daily-tasks/tasks/*-in-scope.yaml` (Target: 3–5): `Pass`
  - Negative boundaries: `7` challenging near-neighbor prompts across `evals/waza/skills/daily-tasks/tasks/*-out-of-scope.yaml` (Target: 3–5): `Pass`
  - Avoidance of trivial negatives: `Pass` (tests boundaries against calendar time-blocking, `para-vault`, `ce-babysit-pr`, `plan-product`, `manage-file-operations`, `write-like-me`, and cross-timezone calendar scheduling)
- **Grader & Assertion Depth**:
  - Meaningful assertions (structural contracts, artifacts, exact phrases): `Rigorous` (`behavior.yaml`, `tasks/behavior/personal-only.yaml`, `fixtures/personal-only/`, and `graders/validate-personal-only.py` ported to `evals/waza/skills/daily-tasks/`, alongside `scenario-catalog.yaml` targeting `daily-tasks`)
- **Matrix & Verification Receipts**:
  - Cross-host matrix & verification summary (`evals/LATEST.md`): `Present`
- **Remediation Steps**:
  - [x] Replace trivial negative prompts in `evals/waza/skills/daily-tasks/tasks/*-out-of-scope.yaml` with challenging near-neighbor negative prompts (calendar time-slot scheduling / Pomodoro time-fitting, filing reference notes into a PARA vault, moving/renaming folders, PR CI babysitting, voice-profile setup, and product roadmap sequencing).
  - [x] Port `behavior.yaml`, `fixtures/personal-only/`, `tasks/behavior/personal-only.yaml`, and `graders/validate-personal-only.py` into `evals/waza/skills/daily-tasks/` and update `scenario-catalog.yaml` (`skill: daily-tasks`).
  - [x] Add evaluation receipts summary at [`evals/LATEST.md`](../../evals/LATEST.md) and update [`evals/README.md`](../../evals/README.md).

---

## Prioritized Remediation Roadmap

1. **Phase 1: High Priority (Structural & Validator Compliance)**
   - [x] Update the top-of-file Scope Directive in all 8 files under [`skills/daily-tasks/references/`](../../skills/daily-tasks/references/) to start with `> [!IMPORTANT] Scope Directive` on the first alert line.
   - [x] Add `## Verification` sections with observable completion checklists to [`skills/daily-tasks/SKILL.md`](../../skills/daily-tasks/SKILL.md) and all 5 workflow files in [`skills/daily-tasks/workflows/`](../../skills/daily-tasks/workflows/).
   - [ ] Resolve the unignored `.nyssa-ai/` root directory violation in [`.gitignore`](../../.gitignore#L9) if strict root-whitelist validation is required.
2. **Phase 2: Medium Priority (Deterministic Boundary & Cognitive Mode Formatting)**
   - [x] Reconcile the instruction drift between `src/daily_tasks/cli.py` (`daily-tasks-mcp`) and the legacy CLI commands referenced in `workflows/records.md`, `workflows/checkin.md`, and `references/*.md`.
   - [x] Convert dense narrative paragraphs in `skills/daily-tasks/workflows/*.md` into structured bulleted directives and checklists, and keep `skills/daily-tasks/references/*.md` focused on domain specifications and prose rationale.
3. **Phase 3: Verification & Packaging (Assembly, Evals & Receipts)**
   - [x] Restore and migrate the behavioral evaluation fixtures and graders (`behavior.yaml`, `fixtures/`, `graders/`) into `evals/waza/skills/daily-tasks/` and update `scenario-catalog.yaml`.
   - [x] Upgrade negative Waza trigger prompts in `evals/waza/skills/daily-tasks/tasks/` from trivial general-knowledge questions to challenging near-neighbor prompts.
   - [x] Run `python scripts/assemble.py write`, `python scripts/assemble.py check`, and `python scripts/validate.py`, and record current evaluation receipts in `evals/LATEST.md`.
