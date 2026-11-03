# Product Roadmap

This document lists delivery steps in build order. `docs/features.md` owns the user-facing feature catalog and functional groupings, `docs/concepts/` owns domain models and cross-feature macro-flows (`C-nn`), and `docs/tech-stack.md` records technology context; this roadmap synthesizes them (along with existing AST symbols when `.codegraph/` is present) into dependency-driven delivery sequencing, architectural rationale, technical guardrails, and verification checkpoints.

---

## How to Use This Roadmap

* **Step IDs (`R-pp.ss`):** Each delivery step uses the `R-pp.ss` scheme, where `pp` is the two-digit Delivery Phase (`00`–`99`) in build order, and `ss` is the sequential Step (`01`–`99`) within that phase. IDs are assigned once and never renumbered; list order determines delivery order.
* **Target Linking:** Each step completes one or more Use Cases, written as `[UC-gg.nn.uu](features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`. When a foundational or setup feature has no separate use cases, the step falls back to linking the feature directly as `[F-gg.nn](features/f-gg.nn/feature.md)`.
* **Planning vs. Implementation Boundary:** Unlike feature guides and use cases (which must remain in non-technical, user-focused language), roadmap steps and `Verify:` checkpoints may include concrete technical delivery decisions, technology selections, symbol anchors, and verification commands. However, roadmap steps must **not** contain source code snippets, function definitions, file-by-file edit tasks, class/call trees, or database DDL schemas—those belong in downstream implementation planning (`/plan` or `ce-plan`).
* **Enriched Step Schema (Field Guide):** Every step captures high-signal sub-bullets under its statement line:
  1. **Statement:** One human-readable statement line: `- [ ] R-pp.ss: Imperative statement — [UC-gg.nn.uu](features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`, with `— after: ...` appended only when the step declares dependencies.
  2. **Rationale (`- Rationale:`):** Causal reason why this step is positioned here and what upstream state or prerequisite capability it relies upon.
  3. **Concepts (`- Concepts:`):** Linked domain models (`[C-nn](concepts/c-nn-short-slug.md)`) and tech-stack capabilities informing this delivery slice.
  4. **Anchors (`- Anchors:`):** *(Conditional: included only when `.codegraph/` is present at the repo root)* Names prerequisite AST symbols consumed and target symbols/interfaces established so `ce-plan` can query them directly via `codegraph_explore`. Omit cleanly when CodeGraph is not active.
  5. **Gotchas (`- Gotchas:`):** Critical architectural constraints, edge cases, or concurrency/idempotency pitfalls to account for without prescribing implementation code.
  6. **Verify (`- Verify:`):** A user-verifiable stopping point describing what the user runs or clicks, what observable outcome confirms success, and demo data when needed. A step with no direct user-observable outcome may defer with `Verify: with R-pp.ss`, naming a later step whose checkpoint demonstrates it (never more than two consecutive open steps defer).
* **Dependencies (`after:`):** An optional `after:` list names prior step IDs (`R-pp.ss`) or feature IDs (`F-gg.nn`) this step must follow. A step must not name its own parent feature or use case.
* **Status:** Check a step only when its work is implemented and verified. Completed steps are immutable history.
* **Coverage:** Every incomplete feature in `docs/features.md` needs step coverage here.
* **Engineering Handoff (`ce-plan`):** Each `R-pp.ss` step is structured as a briefing note for `/plan` or `ce-plan` to initiate technical implementation planning.

---

## Steps

### Phase 01: Foundation, Storage & Read-Only Connectors

- [x] R-01.01: Establish workspace profile resolution, timezone handling, and customizable template management — [UC-00.01.01](features/f-00.01/uc-00.01.01-setup-workspace-and-templates.md)
    - Rationale: All downstream record and planning operations depend on resolved user identity, local timezone, workspace roots, and active templates.
    - Concepts: Informed by [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Establishes `resolveContext`, `planningBinding`, `assertPlanningScope`, and `localDay`.
    - Gotchas: Keep resolved configuration, vault, and projects roots independent of process `cwd`, and never overwrite user-edited templates without explicit confirmation.
    - Verify: Run `npm test` and confirm `test/context.test.mjs` and `test/template-updates.test.mjs` pass.
- [x] R-01.02: Implement immutable domain DTOs, surgical Markdown CST parser/writer, and atomic `LocalFileStore` — [F-00.02](features/f-00.02/feature.md) — after: R-01.01
    - Rationale: Canonical records and daily plans must round-trip without losing user prose or comments before ports or session state machines can read or write them.
    - Concepts: Enforces surgical preservation and record schema invariants in [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Establishes `StateGraph`, `PlanningSession`, `DailyPlanDocument`, `LocalFileStore`, `MarkdownFileStore`, `apply_record_change`, and `render_daily_plan`.
    - Gotchas: Verify `expected_hash` before writing any record so external user edits abort the batch cleanly with a conflict rather than overwriting changes.
    - Verify: Run `uv run pytest test/unit/daily_tasks/domain/ test/unit/daily_tasks/storage/` and confirm all spec round-trip and CST surgical write checks pass.
- [x] R-01.03: Deliver in-memory secret protection, read-only Gmail/Slack communication ports, and incremental cursor persistence — [UC-00.03.01](features/f-00.03/uc-00.03.01-authorize-readonly-communication-source.md) — after: R-01.02
    - Rationale: Background communication ingestion in the planning session requires read-only port protocols, sealed OAuth tokens, and watermark cursor tracking.
    - Concepts: Supports Stage 0 message collection in [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md).
    - Anchors: Consumes `LocalFileStore` (from R-01.02); establishes `ProjectPlanPort`, `DailyPlanPort`, `CommunicationPort`, `GmailOauth`, `SecretResolver`, and `gmail`.
    - Gotchas: Never request send/modify scopes or log unmasked tokens, and isolate failing connectors so one unavailable source does not fail the session.
    - Verify: Run `uv run pytest test/unit/daily_tasks/adapters/ test/unit/daily_tasks/auth/` and confirm read-only connector, cursor, and OAuth CLI tests pass.

### Phase 02: Commitment Capture, Lifecycle Rules & Skill Routing

- [x] R-02.01: Implement candidate work capture, deduplication, and explicit batch acceptance workflows — [UC-01.01.01](features/f-01.01/uc-01.01.01-capture-and-accept-candidate-work.md) — after: R-01.02
    - Rationale: Extracted action items from notes and conversations must be deduplicated and held as candidates before record creation.
    - Concepts: Enforces candidate-vs-accepted separation in [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Consumes `projectInventory` and `taskSummary`; establishes candidate deduplication and acceptance handoff in `skills/daily-tasks-capture/SKILL.md`.
    - Gotchas: Quoted requests and inferred promises must remain candidates until explicitly accepted; direct named creation supplies acceptance immediately.
    - Verify: Run `npm run check` and `npm test` to confirm capture and acceptance validation checks pass.
- [x] R-02.02: Enforce project, milestone, task, and blocker lifecycle rules and embedded Definition of Done verification — [UC-01.02.01](features/f-01.02/uc-01.02.01-update-work-status-and-dod.md) — after: R-01.02, R-02.01
    - Rationale: Record mutations from direct instructions, check-ins, and planning sessions must enforce DoD and blocker completion rules consistently.
    - Concepts: Implements completion and responsibility rules from [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) and [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Consumes `LocalFileStore` (from R-01.02); establishes `derive_task_facts`, `derive_blocker_facts`, and `recordIssueIsInvalid`.
    - Gotchas: Completing a task requires every embedded DoD item checked and zero open blockers; completing or cancelling a milestone requires all child tasks finished or explicitly decided.
    - Verify: Run `uv run pytest test/unit/daily_tasks/graph/` and `npm test` to verify completion guardrail enforcement.
- [x] R-02.03: Assemble canonical skill router, host bundles, and optional project-index prewarm command — [F-03.01](features/f-03.01/feature.md) — after: R-01.01
    - Rationale: Host environments require generated manifests and portable bundles built deterministically from `skills/`.
    - Concepts: Preserves skill routing and non-persona boundaries defined in `docs/product.md`.
    - Anchors: Consumes `resolveContext` (from R-01.01); establishes `assemble.mjs` and `warm-project-index.mjs`.
    - Gotchas: Prewarm must execute exact Node argv with no LLM call or chat output, and every workflow must retain stale-on-demand verification when prewarm is absent.
    - Verify: Run `npm run check` (`node scripts/assemble.mjs check && node scripts/validate.mjs`) and confirm zero manifest drift.

### Phase 03: Deterministic Correlation, Three-Screen Planning & Check-In

- [x] R-03.01: Build in-memory `StateGraph` compilation, deterministic message correlation, and Screen 1 suggestion adjudication — [UC-02.01.01](features/f-02.01/uc-02.01.01-review-and-adjudicate-message-suggestions.md) — after: R-01.03, R-02.02
    - Rationale: Screen 1 requires compiled project/task metrics, rollover candidates, and deterministically matched message suggestions before user adjudication can occur.
    - Concepts: Implements Stage 0 and Stage 1 of [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md) and [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Consumes `ProjectPlanPort`, `DailyPlanPort`, and `CommunicationPort` (from R-01.03); establishes `build_state_graph`, `match_messages`, `parse_verdicts`, and `adjudicate_suggestions`.
    - Gotchas: Suggestions must be numbered after Current Plan rows so earlier row numbers never shift, and messages stay unreviewed until their suggestions are adjudicated.
    - Verify: Run `uv run pytest test/unit/daily_tasks/matching/ test/unit/daily_tasks/session/test_adjudication.py` and confirm deterministic correlation and verdict pruning pass.
- [x] R-03.02: Implement the three-screen session state machine, Screen 2 per-project day assignment, and Screen 3 confirmation — [UC-02.02.01](features/f-02.02/uc-02.02.01-assign-project-tasks-to-days.md), [UC-02.02.02](features/f-02.02/uc-02.02.02-confirm-and-write-daily-plan.md) — after: R-03.01
    - Rationale: Sequences the interactive Screen 1 → Screen 2 → Screen 3 lifecycle, continuous row numbering across Screens 1–2, restarted numbering on Screen 3, and atomic confirmation.
    - Concepts: Enforces [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md), [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md), and [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md).
    - Anchors: Consumes `StateGraph` and `adjudicate_suggestions` (from R-03.01); establishes `SessionStage`, `SessionState`, `apply_operations`, `show_confirm`, `confirm_session`, and `DecisionLogger`.
    - Gotchas: Screen 3 must restart numbering at `1` and reject stale row numbers from Screens 1 and 2; unanswered suggestions must remain in `suggestions.json` after confirmation.
    - Verify: Run `uv run pytest test/unit/daily_tasks/session/` and confirm lifecycle, screen rendering, and confirmation tests pass.
- [x] R-03.03: Deliver anytime check-in and manual Markdown edit reconciliation — [UC-02.03.01](features/f-02.03/uc-02.03.01-reconcile-manual-edits-at-checkin.md) — after: R-02.02
    - Rationale: Users editing checkboxes or text directly in daily plans and project records need anytime reconciliation and resumable conflict resolution.
    - Concepts: Enforces [C-01: Canonical Work Records & Embedded Definition of Done](concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Consumes `planningReview` and `preparePlanning`; establishes `inspectMaintenance` and `verifiedMaintenanceStatus`.
    - Gotchas: Manual checkbox completions in a daily plan must still verify task DoD and blocker rules before closing the canonical task record.
    - Verify: Run `npm test` and confirm `test/maintenance.test.mjs` and `test/planning-recovery.test.mjs` pass.

### Phase 04: Assistant Host Integration, Packaging & Syndication

- [x] R-04.01: Expose the planning session over MCP stdio JSON-RPC transport with stderr-isolated structured logging — [UC-03.02.01](features/f-03.02/uc-03.02.01-run-planning-session-via-assistant-tools.md) — after: R-03.02
    - Rationale: Connects AI assistant hosts to the deterministic 3-screen session engine via standard MCP tool calls while keeping `stdout` pure for JSON-RPC frames.
    - Concepts: Exposes [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md) over the MCP server stack in `docs/tech-stack.md`.
    - Anchors: Consumes `SessionState` and `LocalFileStore` (from R-03.02); establishes `PlanningTools`, `McpServer`, `serve_stdio`, `tool_reply`, `logging_setup`, and `cli`.
    - Gotchas: Out-of-stage tool calls must return a structured `refused` payload naming `expected_tool`, and all diagnostic logs must emit strictly to `sys.stderr`.
    - Verify: Run `uv run pytest test/unit/daily_tasks/server/ test/unit/daily_tasks/integration/test_full_planning_session.py` and confirm all MCP protocol and full-session tests pass.
- [x] R-04.02: Register `daily-tasks-mcp` CLI script entrypoint, update canonical skill documentation for MCP session tools and OAuth onboarding, reassemble host bundles, and complete project syndication — [UC-03.02.01](features/f-03.02/uc-03.02.01-run-planning-session-via-assistant-tools.md) — after: R-02.03, R-04.01
    - Rationale: Completes Milestone M6 (`t2-logging-and-tessl-syndication`) so assistant hosts can launch `daily-tasks-mcp` via `pyproject.toml` and follow updated canonical skill instructions (`daily-tasks`, `daily-tasks-setup`, `daily-tasks-plan`, `daily-tasks-checkin`).
    - Concepts: Completes host integration for [C-04: Three-Screen Planning Session Macro-Flow](concepts/c-04-three-screen-planning-session.md) while preserving [C-02: Local-Day Plan, Rollover & Carried Selections](concepts/c-02-local-day-plan-and-rollover.md) and [C-03: Explicit Adjudication & Decision Log](concepts/c-03-explicit-adjudication-and-decision-log.md) guardrails.
    - Anchors: Consumes `cli` (`src/daily_tasks/cli.py`), `gmail` (`src/daily_tasks/auth/gmail.py`), and `PlanningTools` (`src/daily_tasks/server/planning_tools.py`); establishes entrypoint in `pyproject.toml`, registers tools across `skills/daily-tasks*/SKILL.md`, and updates host plugin manifests via `python scripts/assemble.py write`.
    - Gotchas: Preserve strict "no time-fitting, no implicit acceptance" guardrails in all updated skills, regenerate host manifests with `python scripts/assemble.py write`, and verify `check_adoption.py` and `scripts/validate.py` pass cleanly.
    - Verify: Run `daily-tasks-mcp --help`, `python .nyssa-ai/dev-standards/python/scripts/check_adoption.py . --run`, `python scripts/assemble.py check`, and `python scripts/validate.py`, confirming zero errors and complete Milestone M6 tasks in `projects/2026.11.03-daily-tasks-mcp-server/`.
