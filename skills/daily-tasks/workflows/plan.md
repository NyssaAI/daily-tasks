> [!IMPORTANT] Scope Directive
> This workflow owns creating and updating the user's local-day Markdown plan across personal, delegated, and follow-up work using the 3-screen MCP planning session (`daily_tasks_*` tools). It does NOT own workspace/profile setup (`setup.md`), candidate extraction (`capture.md`), standalone record mutations (`records.md`), full manual-edit check-in reconciliation (`checkin.md`), or planning domain architecture (owned by `../references/planning-flow.md`).

# Plan the day

Execute the interactive daily planning session in order. Reference [planning flow](../references/planning-flow.md) for domain invariants, [response conventions](../references/response-conventions.md) for reply grammar, and [custom templates](../references/templates.md) for layout rules.

## 1. Mandatory presentation and layout gates

- **Screen gate**: Render every task-selection screen, project page, resumed review, and planning recap using the exact `payload.screen` markdown returned by the MCP tool outside code fences. **Never** replace `payload.screen` with a prose summary, plain numbered list, question widget, or the saved daily-plan file layout.
- **Daily plan file gate**: Ensure every created or updated `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` file conforms to the active `dailyPlan` template (by default: `# Daily plan — LOCAL_DATE`, `Open projects: ... Open tasks: ... Late tasks: ...`, `**Timezone:**`, `**Updated:**`, `## Selected for today` with `### My work`, `### Delegated work`, and `### Follow-up work`, `#### PROJECT_TITLE / MILESTONE_TITLE` subheadings, 6-column tables `| # | Status | Project | Milestone | Task | Due Date |` with escaped wiki-link pipes `[[relative-path\|Task title]] <!-- ref: UUID -->`, `Legend:`, `## Blockers`, `## Decisions`, and `## Notes and references`). Never substitute `- [ ]` bullet checklists unless the active `dailyPlan` template explicitly uses checklists.
- **No time-fitting gate**: Never rank selections, request an execution-order decision, estimate durations, schedule time slots, or fit tasks into a time budget.

## 2. Pre-flight and workspace preparation

1. **Enforce all four full-setup gates**:
   - Confirm that `daily_tasks_*` MCP tools are registered and callable in the active harness, `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` exists with `"schema_version": 2`, `projectsRoot`, `dailyPlansRelative`, and `sources`, layered profile resolution supplies `user.email` and an explicit IANA `timezone`, and `<workspaceRoot>/.nyssa-ai/daily-tasks/templates/updates.json` is present ([resolve once](../references/planning-flow.md#resolve-once)).
   - If **any** setup gate fails (including missing `daily_tasks_*` MCP tools or an unmigrated legacy `.nyssaai/daily-tasks/profile.json`), **immediately halt** planning and execute [Setup](setup.md) first. **Never** read vault Markdown files to synthesize a prose summary or run ad-hoc Python scripts when setup or MCP tools are missing.
   - Check [template updates](../references/template-updates.md) only when `shouldOfferTemplates` is true.
   - When manual edits or conflicts are reported prior to planning, reconcile affected baselines per [operations](../references/operations.md) and [record conventions](../references/records.md), and run the daily source scan via [Capture](capture.md) if `sources.autoScan` is enabled and `<stateRoot>/source-scans/YYYY.MM.DD.json` is absent.

### Existing assistant connections

When the workspace profile configures `sources.harnessConnections`, ingest unread messages before calling `daily_tasks_start_session`:
1. Call `daily_tasks_get_fetch_window(sources=[...], workspace_root?)` for the configured `source` names to obtain each source's `since` (ISO UTC), `after_epoch` (Unix seconds), `last_external_id`, and `has_cursor`.
2. Read messages at or after `since` using the host's existing integration in strictly **read-only** mode (never send, reply, draft, label, archive, or mark read).
3. Map each message to `docs/specs/message.json` (`id` as `<source>:<external_id>`, `source`, `external_id`, `thread_id`, `received_at`, `from`, `to`, `cc`, `channel`, `subject`, `snippet`, `body`, `body_format`, `attachments`, `url`, `fetched_at` with UTC `Z` timestamps).
4. Pass `messages=[...]` and `checked_sources=[...]` (including every successfully checked source even if 0 messages arrived) to `daily_tasks_start_session`. If a host connection fails, report that the source was skipped and omit it from `checked_sources`.

## 3. Execute the 3-screen MCP planning session

Run the session strictly via `daily_tasks_*` MCP tools (never invoke `daily-tasks-mcp` or `python -m daily_tasks.server` as a shell command):

1. **Screen 1 — Start session & review suggestions (`daily_tasks_start_session`)**:
   - Call `daily_tasks_start_session(date?, focus?, messages?, checked_sources?, workspace_root?)` (omit `date` unless planning a specific requested date; pass `workspace_root` if the host runs without `--workspace-root`).
   - If `payload.malformed_files` is non-empty, alert the user immediately with the file paths and error codes, and invoke [Records](records.md) to surgically repair the malformed files before continuing.
   - Display the returned Screen 1 `payload.screen` unchanged (showing carried-forward work `↺` and numbered message-derived suggestions).
2. **Adjudicate replies (`daily_tasks_execute_operations`)**:
   - Interpret user replies using [response conventions](../references/response-conventions.md), [review scope](../references/planning-flow.md#review-scope), and [durable mapping](../references/planning-flow.md#build-and-review).
   - Call `daily_tasks_execute_operations(session_id, original_words, verdicts?, operations?)` where:
     - `verdicts` contains `{"row", "verdict": "accept" | "edit" | "reject", "edits"?}` for suggestion rows.
     - `operations` conforms to `docs/specs/operations.json` (`assign-to-day`, `unplan`, `set-status`, `reassign`).
   - **Never** fabricate a verdict the user did not give: a bare row number, silence, or `"ok"` is not acceptance. Prompt for clarification on ambiguous row numbers while staging unambiguous items.
   - Route new text-only checkboxes or quoted requests to [Capture](capture.md) as candidates, and standalone blocker/closure updates to [Records](records.md).
3. **Screen 2 — Per-project task assignment (`daily_tasks_advance_screen`)**:
   - Call `daily_tasks_advance_screen(session_id, target_screen=2)` when the user says `"yes"` (first project) or `"next"` (subsequent project page), and render `payload.screen` unchanged.
   - Apply task selections (`assign-to-day`), deselections (`unplan`), status updates (`set-status`), or delegations (`reassign`) via `daily_tasks_execute_operations`.
4. **Screen 3 — Confirmation recap (`daily_tasks_advance_screen`)**:
   - Call `daily_tasks_advance_screen(session_id, target_screen=3)` when the user says `"finish"`, and render the Screen 3 recap `payload.screen` unchanged.
5. **Commit or cancel (`daily_tasks_confirm_plan` / `daily_tasks_cancel_session`)**:
   - Call `daily_tasks_confirm_plan(session_id, confirmed=true)` **only** after the user explicitly confirms the Screen 3 recap. This surgically updates modified records, renders `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` per the [saved-plan contract](../references/planning-flow.md#saved-daily-plan), appends `<stateRoot>/decision-log.json`, and saves `<stateRoot>/fetch-cursors.json`.
   - Call `daily_tasks_cancel_session(session_id)` if the user aborts (discards staged state without touching disk), or `daily_tasks_get_session_state(session_id)` to re-display the active screen.

## Verification

Before reporting completion of a daily planning step or session:
- [ ] Confirm `daily-tasks-mcp` was used exclusively via `daily_tasks_*` MCP tool calls and never executed via shell or CLI.
- [ ] Confirm every interactive screen rendered the exact `payload.screen` returned by the MCP server without prose substitution or time-slot scheduling.
- [ ] Confirm any reported `payload.malformed_files` were surfaced to the user and surgically repaired via [Records](records.md).
- [ ] When the plan was confirmed (`daily_tasks_confirm_plan(confirmed=true)`), verify `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` exists on disk, matches the active `dailyPlan` template, and is linked in the response.
