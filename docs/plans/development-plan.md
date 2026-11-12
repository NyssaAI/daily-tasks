# Development Plan

This document lists delivery steps in build order. `docs/features.md` owns the user-facing feature catalog and functional groupings, `docs/concepts/` owns domain models and cross-feature macro-flows (`C-nn`), and `docs/tech-stack.md` records technology context; this development plan synthesizes them (along with tracked AST symbols in `docs/code-map/codegraph.db`) into dependency-driven delivery sequencing, architectural rationale, technical guardrails, and verification checkpoints.

---

## How to Use This Development Plan

* **Step IDs (`DP-pp.ss`):** Each delivery step uses the `DP-pp.ss` scheme, where `pp` is the two-digit Delivery Phase (`00`–`99`) in build order, and `ss` is the sequential Step (`01`–`99`) within that phase. IDs are assigned once and never renumbered; list order determines delivery order.
* **Target Linking:** Each step completes one or more Use Cases, written as `[UC-gg.nn.uu](../features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`. When a foundational or setup feature has no separate use cases, the step falls back to linking the feature directly as `[F-gg.nn](../features/f-gg.nn/feature.md)`.
* **Planning vs. Implementation Boundary:** Unlike feature guides and use cases (which remain in non-technical, user-focused language), development plan steps and `Verify:` checkpoints may include concrete technical delivery decisions, technology selections, symbol anchors, and verification commands. However, steps must **not** contain source code snippets, function definitions, file-by-file edit tasks, class/call trees, or database DDL schemas—those belong in step-linked implementation plans (`docs/plans/dp-pp.ss-<slug>.md`).
* **Enriched Step Schema (Field Guide):** Every step captures high-signal sub-bullets under its statement line:
  1. **Statement:** One human-readable statement line: `- [ ] DP-pp.ss: Imperative statement — [UC-gg.nn.uu](../features/f-gg.nn/uc-gg.nn.uu-short-slug.md)`, with `— after: ...` appended only when the step declares dependencies.
  2. **Rationale (`- Rationale:`):** Causal reason why this step is positioned here and what upstream state or prerequisite capability it relies upon.
  3. **Concepts (`- Concepts:`):** Linked domain models (`[C-nn](../concepts/c-nn-short-slug.md)`) and tech-stack capabilities informing this delivery slice.
  4. **Anchors (`- Anchors:`):** Names prerequisite AST symbols consumed and target symbols/interfaces established so implementation planning can query them directly via `codegraph_explore`.
  5. **Gotchas (`- Gotchas:`):** Critical architectural constraints, edge cases, or concurrency/idempotency pitfalls to account for without prescribing implementation code.
  6. **Verify (`- Verify:`):** A user-verifiable stopping point describing what the user runs, what observable outcome confirms success, and demo data when needed. A step with no direct user-observable outcome may defer with `Verify: with DP-pp.ss`, naming a later step whose checkpoint demonstrates it (never more than two consecutive open steps defer).
* **Dependencies (`after:`):** An optional `after:` list names prior step IDs (`DP-pp.ss`) or feature IDs (`F-gg.nn`) this step must follow. A step must not name its own parent feature or use case.
* **Status:** Check a step only when its work is implemented and verified. Completed steps are immutable history.
* **Coverage:** Every incomplete feature in `docs/features.md` needs step coverage here.
* **Engineering Handoff:** Each `DP-pp.ss` step serves as a briefing note for technical slice planning (`docs/plans/dp-pp.ss-<slug>.md`).

---

## Steps

### Phase 01: Foundation, Record Persistence & Read-Only Communication Clients

- [x] DP-01.01: Establish vault profile resolution, timezone handling, and customizable template management — [UC-00.01.01](../features/f-00.01/uc-00.01.01-setup-vault-and-templates.md)
    - Rationale: All downstream record and planning operations depend on resolved user identity, local timezone, `vault_root` / `runtime_root` paths, and active templates.
    - Concepts: Informed by [C-01: Canonical Work Records & Embedded Definition of Done](../concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](../concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Establishes `ProfileStore`, `resolve_runtime_root`, `resolve_server_settings`, `SetupTools`, and `TemplateSynchronizer`.
    - Gotchas: Keep resolved configuration (`user_home` -> `repo_root`), `vault_root` (`1-projects`, `2-areas/daily-plans`, zero `.nyssa-ai/` inside vault), and `runtime_root` independent, reject agent runtime directories (`SOUL.md` + `IDENTITY.md`) as `vault_root`, and never overwrite user-edited templates without explicit confirmation.
    - Verify: Run `uv run pytest test/unit/daily_tasks/hosting/` and confirm `test_resolve_runtime_root.py`, `test_resolve_server_settings.py`, and `test_setup_tools.py` pass.
- [x] DP-01.02: Implement immutable domain entities, non-destructive Markdown CST parser/writer, and atomic `FileStoreLocal` — [F-00.02](../features/f-00.02/feature.md) — after: DP-01.01
    - Rationale: Canonical records and daily plans must round-trip without losing user prose or comments before repositories or session state machines can read or write them.
    - Concepts: Enforces non-destructive edit preservation and record schema invariants in [C-01: Canonical Work Records & Embedded Definition of Done](../concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](../concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Establishes `RecordKind`, `StateGraph`, `PlanningSession`, `DailyPlanDocument`, `FileStore`, `FileStoreLocal`, `ProjectPlanRepositoryMarkdown`, `DailyPlanRepositoryMarkdown`, `apply_record_change`, and `render_daily_plan`.
    - Gotchas: Verify `expected_hash` before writing any record so external user edits abort the batch cleanly with a conflict rather than overwriting changes.
    - Verify: Run `uv run pytest test/unit/daily_tasks/core/records/ test/unit/daily_tasks/records/` and confirm all spec round-trip and CST non-destructive write checks pass.
- [x] DP-01.03: Deliver in-memory secret protection, read-only Gmail/Slack communication clients, and incremental cursor persistence — [UC-00.03.01](../features/f-00.03/uc-00.03.01-authorize-readonly-communication-source.md) — after: DP-01.02
    - Rationale: Background communication retrieval in the planning session requires read-only `CommunicationClient` implementations, sealed OAuth tokens, and watermark cursor tracking in `runtime_root`.
    - Concepts: Supports Stage 0 message collection in [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md).
    - Anchors: Consumes `FileStore` (from DP-01.02); establishes `ProjectPlanRepository`, `DailyPlanRepository`, `CommunicationClient`, `CommunicationClientGmail`, `CommunicationClientSlack`, `CursorStoreJson`, `GmailOauth`, `SecretString`, `SecretResolver`, and `SecretCaptureService`.
    - Gotchas: Never request send/modify scopes or log unmasked tokens, and isolate failing clients so one unavailable source does not fail the session.
    - Verify: Run `uv run pytest test/unit/daily_tasks/communications/` and confirm read-only client, cursor, secret, and OAuth CLI tests pass.

### Phase 02: Commitment Capture, Lifecycle Rules & Skill Routing

- [x] DP-02.01: Implement candidate work capture, deduplication, and explicit batch acceptance workflows — [UC-01.01.01](../features/f-01.01/uc-01.01.01-capture-and-accept-candidate-work.md) — after: DP-01.02
    - Rationale: Extracted action items from notes and conversations must be deduplicated and held as candidates before record creation.
    - Concepts: Enforces candidate-vs-accepted separation in [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Establishes candidate deduplication and acceptance handoff in `skills/daily-tasks/workflows/capture.md`.
    - Gotchas: Quoted requests and inferred promises must remain candidates until explicitly accepted; direct named creation supplies acceptance immediately.
    - Verify: Run `python scripts/validate.py` to confirm capture workflow integrity and cross-links pass.
- [x] DP-02.02: Enforce project, milestone, task, and blocker lifecycle rules and embedded Definition of Done verification — [UC-01.02.01](../features/f-01.02/uc-01.02.01-update-work-status-and-dod.md) — after: DP-01.02, DP-02.01
    - Rationale: Record mutations from direct instructions, check-ins, and planning sessions must enforce DoD and blocker completion rules consistently.
    - Concepts: Implements completion and responsibility rules from [C-01: Canonical Work Records & Embedded Definition of Done](../concepts/c-01-canonical-work-records.md) and [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Consumes `FileStore` (from DP-01.02); establishes `derive_task_facts`, `derive_blocker_facts`, and `build_state_graph`.
    - Gotchas: Completing a task requires every embedded DoD item checked and zero open blockers; completing or cancelling a milestone requires all child tasks finished or explicitly decided.
    - Verify: Run `uv run pytest test/unit/daily_tasks/core/records/` to verify completion guardrail enforcement.
- [x] DP-02.03: Assemble canonical facade skill router, `harness-adapter` manifests, and `.temp/dist/` host bundles — [F-03.01](../features/f-03.01/feature.md) — after: DP-01.01
    - Rationale: Host environments require generated `harness-adapter` manifests and staged bundles built deterministically from `skills/` and `src/`.
    - Concepts: Preserves skill routing and non-persona boundaries defined in `docs/product.md`.
    - Anchors: Establishes `scripts/assemble.py`, `scripts/validate.py`, and `harness-adapters/hermes/__init__.py`.
    - Gotchas: Stage bundles strictly under `<repo_root>/.temp/dist/` (or `--output-dir`) with zero self-loaded plugin trees or `${PLUGIN_DATA}` references.
    - Verify: Run `python scripts/assemble.py check && python scripts/validate.py` and confirm zero manifest drift.

### Phase 03: Deterministic Correlation, Three-Screen Planning & Check-In

- [x] DP-03.01: Build in-memory `StateGraph` compilation, deterministic message correlation, and Screen 1 suggestion adjudication — [UC-02.01.01](../features/f-02.01/uc-02.01.01-review-and-adjudicate-message-suggestions.md) — after: DP-01.03, DP-02.02
    - Rationale: Screen 1 requires compiled project/task metrics, rollover candidates, and deterministically matched message suggestions before user adjudication can occur.
    - Concepts: Implements Stage 0 and Stage 1 of [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md) and [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md).
    - Anchors: Consumes `ProjectPlanRepository`, `DailyPlanRepository`, and `CommunicationClient` (from DP-01.03); establishes `build_state_graph`, `match_messages`, `parse_verdicts`, and `adjudicate_suggestions`.
    - Gotchas: Suggestions must be numbered after Current Plan rows so earlier row numbers never shift, and messages stay unreviewed until their suggestions are adjudicated.
    - Verify: Run `uv run pytest test/unit/daily_tasks/core/communications/ test/unit/daily_tasks/core/planning/test_adjudication.py` and confirm deterministic correlation and verdict pruning pass.
- [x] DP-03.02: Implement the three-screen session state machine, Screen 2 per-project day assignment, and Screen 3 confirmation — [UC-02.02.01](../features/f-02.02/uc-02.02.01-assign-project-tasks-to-days.md), [UC-02.02.02](../features/f-02.02/uc-02.02.02-confirm-and-write-daily-plan.md) — after: DP-03.01
    - Rationale: Sequences the interactive Screen 1 → Screen 2 → Screen 3 lifecycle, continuous row numbering across Screens 1–2, restarted numbering on Screen 3, and atomic confirmation.
    - Concepts: Enforces [C-02: Local-Day Plan, Rollover & Carried Selections](../concepts/c-02-local-day-plan-and-rollover.md), [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md), and [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md).
    - Anchors: Consumes `StateGraph` and `adjudicate_suggestions` (from DP-03.01); establishes `SessionStage`, `SessionState`, `apply_operations`, `show_confirm`, `ConfirmPlan`, `SessionCommitterLocal`, and `DecisionLogger`.
    - Gotchas: Screen 3 must restart numbering at `1` and reject stale row numbers from Screens 1 and 2; unanswered suggestions must remain in `<runtime_root>/suggestions.json` after confirmation.
    - Verify: Run `uv run pytest test/unit/daily_tasks/core/planning/ test/unit/daily_tasks/planning/` and confirm lifecycle, screen rendering, and confirmation tests pass.
- [x] DP-03.03: Deliver anytime check-in and manual Markdown edit reconciliation — [UC-02.03.01](../features/f-02.03/uc-02.03.01-reconcile-manual-edits-at-checkin.md) — after: DP-02.02
    - Rationale: Users editing checkboxes or text directly in daily plans and project records need anytime reconciliation and resumable conflict resolution.
    - Concepts: Enforces [C-01: Canonical Work Records & Embedded Definition of Done](../concepts/c-01-canonical-work-records.md) and [C-02: Local-Day Plan, Rollover & Carried Selections](../concepts/c-02-local-day-plan-and-rollover.md).
    - Anchors: Establishes check-in reconciliation rules in `skills/daily-tasks/workflows/checkin.md` and `skills/daily-tasks/references/operations.md`.
    - Gotchas: Manual checkbox completions in a daily plan must still verify task DoD and blocker rules before closing the canonical task record.
    - Verify: Run `python scripts/validate.py` and confirm check-in workflow and reconciliation rules validate cleanly.

### Phase 04: Assistant Host Integration & MCP Transport

- [x] DP-04.01: Expose the planning session over MCP stdio JSON-RPC transport with stderr-isolated structured logging — [UC-03.02.01](../features/f-03.02/uc-03.02.01-run-planning-session-via-assistant-tools.md) — after: DP-03.02
    - Rationale: Connects AI assistant hosts to the deterministic 3-screen session engine via standard MCP tool calls while keeping `stdout` pure for JSON-RPC frames.
    - Concepts: Exposes [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md) over the MCP server stack in `docs/tech-stack.md`.
    - Anchors: Consumes `SessionState` and `FileStore` (from DP-03.02); establishes `PlanningToolsDispatcher`, `McpServer`, `serve_stdio`, `compose_mcp_server`, `logging_setup`, and `cli`.
    - Gotchas: Out-of-stage tool calls must return a structured `refused` payload naming `expected_tool`, and all diagnostic logs must emit strictly to `sys.stderr`.
    - Verify: Run `uv run pytest test/unit/daily_tasks/transports/mcp/ test/use_case/daily_tasks/test_full_planning_session.py` and confirm all MCP protocol and full-session tests pass.
- [x] DP-04.02: Register `daily-tasks-mcp` CLI entrypoint, update canonical skill documentation for MCP session tools and OAuth onboarding, and stage host bundles — [UC-03.02.01](../features/f-03.02/uc-03.02.01-run-planning-session-via-assistant-tools.md) — after: DP-02.03, DP-04.01
    - Rationale: Enables assistant hosts to launch `daily-tasks-mcp` via `pyproject.toml` and follow canonical workflow instructions (`skills/daily-tasks/workflows/{setup,plan,checkin,capture,records}.md`).
    - Concepts: Completes host integration for [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md) while preserving [C-02: Local-Day Plan, Rollover & Carried Selections](../concepts/c-02-local-day-plan-and-rollover.md) and [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md) guardrails.
    - Anchors: Consumes `cli` (`src/daily_tasks/cli.py`), `gmail` (`src/daily_tasks/communications/gmail.py`), and `PlanningToolsDispatcher` (`src/daily_tasks/core/planning/planning_tools_dispatcher.py`); establishes entrypoint in `pyproject.toml`, registers tools across `skills/daily-tasks/`, and updates host plugin manifests via `python scripts/assemble.py write`.
    - Gotchas: Preserve strict "no time-fitting, no implicit acceptance" guardrails in all workflows, regenerate host manifests with `python scripts/assemble.py write`, and verify AST checks and `scripts/validate.py` pass cleanly.
    - Verify: Run `daily-tasks-mcp --help`, `python scripts/assemble.py check`, and `python scripts/validate.py`, confirming zero errors.

### Phase 05: Harness Connection Discovery, Configurable 7-Day Lookback & Shared Cursor Retrieval

- [x] DP-05.01: Enforce a configurable 7-day default initial lookback window across `ServerSettings`, `CommunicationClientGmail`, `CommunicationClientSlack`, and `CursorStore` fetch-window calculation — [UC-00.04.01](../features/f-00.04/uc-00.04.01-discover-connections-and-configure-lookback.md), [UC-00.04.02](../features/f-00.04/uc-00.04.02-fetch-messages-via-existing-connection.md) — after: DP-01.03, DP-04.02
    - Rationale: When no saved cursor exists for a communication source (first pull), message retrieval must default to no more than 7 days (`initial_lookback_days = 7`) and honor user-configured overrides in `profile.json` (`sources.initialLookbackDays`) or CLI flags (`--initial-lookback-days`).
    - Concepts: Enforces Stage 0 bounded message collection in [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md).
    - Anchors: Updates `CommunicationClientGmail`, `CommunicationClientSlack`, `ServerSettings`, and `cli`; establishes `DEFAULT_INITIAL_LOOKBACK_DAYS` and `compute_fetch_window`.
    - Gotchas: Reject non-positive `initial_lookback_days` values cleanly, ensure existing saved cursors in `<runtime_root>/fetch-cursors.json` always take precedence over `initial_lookback_days`, and wire `CursorStoreJson` into `compose_mcp_server.py` so `VaultReaderMarkdown` and `SessionCommitterLocal` persist cursors on confirmation.
    - Verify: Run `uv run pytest test/unit/daily_tasks/communications/` and confirm first-pull lookback defaults to 7 days and respects configured overrides while subsequent pulls use the saved cursor.
- [x] DP-05.02: Expose MCP fetch-window inspection (`daily_tasks_get_fetch_window`) and host-supplied message pass-through on `daily_tasks_start_session` sharing `CursorStore` and deterministic correlation — [UC-00.04.02](../features/f-00.04/uc-00.04.02-fetch-messages-via-existing-connection.md) — after: DP-05.01
    - Rationale: Allows AI assistant harnesses (Claude, Codex, Hermes, Antigravity) that already have email or chat connected to query the per-source fetch window (`since` / `after_epoch` and `last_external_id`), fetch messages via their existing connection, and pass them into `daily_tasks_start_session` so the exact same cursor filtering, task correlation, suggestion generation, and cursor advancement run identically.
    - Concepts: Implements [C-03: Explicit Adjudication & Decision Log](../concepts/c-03-explicit-adjudication-and-decision-log.md) and [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md) for harness-connected communication sources.
    - Anchors: Consumes `CursorStore`, `match_messages`, and `generate_suggestions`; establishes `daily_tasks_get_fetch_window`, `filter_harness_messages`, and `messages` parameter on `PlanningToolsDispatcher.start_session` and `TOOL_DEFINITIONS`.
    - Gotchas: Deterministically filter out any host-supplied message at or before `previous.since` (or with `external_id == previous.last_external_id`) or older than the first-pull lookback cutoff, merge host-supplied and client-fetched messages without duplicate cursor collisions, and advance cursors on disk only when `daily_tasks_confirm_plan(confirmed=True)` succeeds.
    - Verify: Run `uv run pytest test/unit/daily_tasks/transports/mcp/test_mcp_server.py` and confirm `daily_tasks_get_fetch_window` returns the 7-day window on first pull, `daily_tasks_start_session` with host-supplied messages generates numbered Screen 1 suggestions and stages cursor advancement, and `daily_tasks_confirm_plan` persists the updated cursor to `fetch-cursors.json`.
- [x] DP-05.03: Update `skills/daily-tasks/workflows/{setup,plan}.md` to detect existing harness connections, ask user preference, configure initial lookback days, and stage host bundles — [UC-00.04.01](../features/f-00.04/uc-00.04.01-discover-connections-and-configure-lookback.md), [UC-00.04.02](../features/f-00.04/uc-00.04.02-fetch-messages-via-existing-connection.md) — after: DP-05.02
    - Rationale: Setup must inspect available email/chat integrations in the user's assistant harness before prompting for standalone credentials, ask the user what they want to use, let them configure the initial lookback window (defaulting to 7 days), and guide the planning workflow to pull via `daily_tasks_get_fetch_window` + existing harness connection when configured.
    - Concepts: Preserves read-only communication boundaries and explicit user choice in `docs/product.md` and [C-04: Three-Screen Planning Session Macro-Flow](../concepts/c-04-three-screen-planning-session.md).
    - Anchors: Updates `skills/daily-tasks/workflows/setup.md`, `skills/daily-tasks/workflows/plan.md`, `skills/daily-tasks/references/cli.md`, and `skills/daily-tasks/references/planning-flow.md`; stages `.temp/dist/` via `python scripts/assemble.py write`.
    - Gotchas: Never invoke outbound send/reply/modify tools on harness connections, preserve existing profile settings on re-entry, and ensure `python scripts/assemble.py check` and `python scripts/validate.py` pass with zero drift.
    - Verify: Run `python scripts/assemble.py write`, `python scripts/assemble.py check`, and `python scripts/validate.py`, and confirm all skill links and bundle manifests validate cleanly.
