---
name: daily-tasks-plan
description: Create or edit the user's local-day Markdown plan across personal and delegated work; review available work and carry unfinished selected work forward without ranking, scheduling or fitting durations. Use for "plan my day," selecting accepted tasks for today or a future day, or adding or removing daily selections; selection does not change task status.
---

# Plan the day

Follow these checkpoints in order. A directly activated Plan uses the same contracts
as router-led planning; no earlier router load is required.

**Screen gate:** Every actual task-selection screen, page, resumed review and planning
recap must use the validated planning session screen. Do not replace it with a prose summary,
plain numbered list, question widget or the saved daily-plan layout. Display the MCP tool's
returned `payload.screen` unchanged. This gate does not apply to explanations of how the plugin
works or a status-only reply that presents no planning options. Explicit user formatting changes
go through template selection/overrides; never silently substitute a different layout.

**Daily plan gate:** Every newly created or updated `YYYY.MM.DD-daily-plan.md` file must
match the active `dailyPlan` template (by default: `# Daily plan — LOCAL_DATE`,
`Open projects: ... Open tasks: ... Late tasks: ...`, `**Timezone:**`, `**Updated:**`,
`## Selected for today` with `### My work`, `### Delegated work`, and `### Follow-up work`,
`#### PROJECT_TITLE / MILESTONE_TITLE` subheadings, 6-column tables
`| # | Status | Project | Milestone | Task | Due Date |` with escaped wiki-link pipes
`[[relative-path\|Task title]] <!-- ref: UUID -->`, `Legend:`, `## Blockers`, `## Decisions`,
and `## Notes and references`). Never replace the template's tables with a `- [ ]` bullet
checklist unless the active `dailyPlan` template explicitly uses checklists.

## MCP planning session

Run the daily planning session through the `daily_tasks_*` MCP tools exposed by `daily-tasks-mcp`.
The planning server must ONLY be used via MCP tools (`daily_tasks_*`); never attempt to execute
`daily-tasks-mcp` or `python -m daily_tasks.server` as a shell command.
The server is deterministic: you turn the user's replies into structured arguments; it validates,
numbers rows, and writes only on confirmation. Display each returned `payload.screen` unchanged.

1. `daily_tasks_start_session(date?, focus?, messages?, checked_sources?)` returns `session_id`
   and screen 1 (plan the day), with carried-forward work (`↺`) and pending suggestions
   pre-matched from unread messages. Nothing is written to disk. For sources set up as existing
   assistant connections, first follow [harness connections](#existing-assistant-connections).
2. `daily_tasks_execute_operations(session_id, original_words, verdicts?, operations?)`
   applies the user's explicit replies all-or-nothing: `verdicts` are
   `{"row", "verdict": "accept" | "edit" | "reject", "edits"?}` for suggestion rows on the
   current screen; `operations` follow `docs/specs/operations.json` (`assign-to-day`,
   `unplan`, `set-status`, `reassign`). Decisions and record changes stay staged in memory.
3. `daily_tasks_advance_screen(session_id, target_screen)`: `2` after the user says "yes"
   (first project) or "next" (next project), `3` after "finish" (recap).
4. `daily_tasks_confirm_plan(session_id, confirmed)` only after the user explicitly
   confirms the recap; pass `confirmed: true`. It applies staged record changes surgically,
   writes the daily plan, appends the decision log, and saves fetch cursors.
5. `daily_tasks_cancel_session(session_id)` discards everything without modifying disk records;
   `daily_tasks_get_session_state(session_id)` re-shows the current screen.

### Existing assistant connections

When the profile lists `sources.harnessConnections`, read those sources through the host's own
connection before starting the session, so they share cursors and matching with standalone connectors:

1. Call `daily_tasks_get_fetch_window(sources=[...])` with the configured `source` names. Each
   `fetch_windows[]` entry gives `since` (ISO UTC), `after_epoch` (Unix seconds, e.g. Gmail
   `after:`), `last_external_id` and `has_cursor`. Without a saved cursor, `since` is the initial
   lookback (7 days by default, `initial_lookback_days`); with one, it is the saved cursor.
2. Read the new messages at or after `since` with the host's existing tool, strictly read-only: never
   send, reply, draft, label, archive or mark messages read. Map each to `docs/specs/message.json`
   (`id` as `<source>:<external_id>`, `source`, `external_id`, `thread_id`, `received_at`, `from`,
   `to`, `cc`, `channel`, `subject`, `snippet`, `body`, `body_format`, `attachments`, `url`,
   `fetched_at`; timestamps in UTC ending in `Z`).
3. Pass them as `daily_tasks_start_session(messages=[...], checked_sources=[...])`, naming every
   source you read in `checked_sources`, even one with no new messages. The server drops messages at
   or before the cursor, older than the first-pull cutoff or equal to `last_external_id`, then matches
   the rest exactly like connector messages. Cursors are saved only by
   `daily_tasks_confirm_plan(confirmed=true)`; a cancelled session leaves them unchanged.

If a host connection fails, tell the user that source was skipped, leave it out of
`checked_sources` and continue planning. A `Validation` error means a message object did not match
the spec; fix the mapping rather than dropping fields the user needs.

Never send a verdict the user did not give: a bare row number, silence or "ok" to a
screen is not acceptance, and unanswered suggestions stay pending. Never add durations,
time slots or capacity fitting. A `refused` result names `expected_tool`; follow it. An
`error` result is reported to the user as-is.

## 1. Resolve and prepare

If project setup is not already done (missing workspace profile or unresolved bindings like
`user.email`, `timezone`, `projectsRoot`, or `dailyPlansRelative`), automatically trigger and run
[Setup](../daily-tasks-setup/SKILL.md) first to complete workspace and user configuration before
starting the planning session.

When `daily_tasks_start_session` or `daily_tasks_get_session_state` reports skipped malformed files
(in `payload.malformed_files` or tool message), alert the user immediately with the file paths and
error details, and trigger [Records](../daily-tasks-records/SKILL.md) to surgically repair them so
those records can be included in the planning session.

Consult [context and planning flow](../daily-tasks/references/planning-flow.md#resolve-once)
only if workspace binding is ambiguous. Reuse the configured profile and
already-loaded guidance. Use [Setup](../daily-tasks-setup/SKILL.md) only for unresolved
settings or an explicit configuration change; do not restart setup for a configured user.
Bind one workspace, its assigned `projectsRoot` and `dailyPlansRoot` throughout this session,
numbered replies and recovery. Shared preferences never combine workspaces.

Daily output is `<workspaceRoot>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md`, normally
`daily-plans` (or `2-areas/daily-plans`), resolved from the profile. Never use `configRoot`,
operating state or a later cwd as output. Setup resolves its known default; ask only if
scope remains unknown or points into configuration/state storage.

When `shouldOfferTemplates` is `false` (`templates` have no unbaselined observations or
pending update offers), proceed without reading [template updates](../daily-tasks/references/template-updates.md).
Otherwise retain an observed baseline, offer relevant changes and continue with the active layout
while an update is undecided. Saved-plan and chat-review choices are independent.

## 2. Recover and reconcile

When no manual edits or conflicts are reported, proceed directly to the planning session
without reading [operations](../daily-tasks/references/operations.md) or
[record conventions](../daily-tasks/references/records.md). Otherwise inspect current-plan
edits and per-view baselines, and recover applicable pending operations before applying
affected changes. Preserve unresolved references instead of guessing identity.

Compare edits before regenerating any view; suspend only conflicting items and
continue independent changes. When `sources.autoScan` is enabled and no scan receipt
exists in `stateRoot/source-scans/YYYY.MM.DD.json`, run the daily source scan via
[Capture](../daily-tasks-capture/SKILL.md). Manual status edits update canonical records through
[Records](../daily-tasks-records/SKILL.md); unidentified new checkboxes go to
[Capture](../daily-tasks-capture/SKILL.md) as candidates.

## 3. Carry-forward and Screen 1 (Plan the Day)

`daily_tasks_start_session` deterministically computes once-per-day carry-forward (`↺`) from
the nearest earlier daily plan and builds Screen 1:
- Preserves an existing plan's UUID, original `created_at`, selections, prose and valid edits.
- Carries in-progress tasks and unfinished prior selections forward unless explicitly deselected.
- Gathers unread email and chat messages via configured read-only connectors and host-supplied
  `messages` from existing assistant connections, correlates them against the state graph, and
  presents numbered update suggestions with cited sources.

## 4. Screen 2 (Assign Tasks to Days) and Screen 3 (Confirm Plan)

Consult [review scope](../daily-tasks/references/planning-flow.md#review-scope),
[durable mapping](../daily-tasks/references/planning-flow.md#build-and-review)
and [response conventions](../daily-tasks/references/response-conventions.md) when
interpreting numbered replies or custom formatting. Scoped review presents all-owner visibility,
stable ordering, lowest incomplete milestones, and one project per page.

Display each screen's `payload.screen` unchanged outside code fences.
When authoring or updating documents, use the active template per
[custom templates](../daily-tasks/references/templates.md) and follow the
[saved-plan contract](../daily-tasks/references/planning-flow.md#saved-daily-plan)
for section separation (`My work`, `Delegated work`, `Follow-up work`) and retaining only selected work.

## 5. Apply explicit decisions

Resolve replies against the current screen using response conventions. A bare number
needs an action; clarify only affected items, retain clear batch decisions and save
progress before waiting. Silence and omitted rows never supply acceptance.
Adding unselected not-started work requires an explicit planning decision (`assign-to-day`).
Removing a not-started row (`unplan`) deselects it and stops future carry until re-selected.
For in-progress rows, request rescheduling, completion or cancellation; they cannot
silently drop from plans.

Status, ownership, or closure changes go through `daily_tasks_execute_operations` or
[Records](../daily-tasks-records/SKILL.md). Quoted requests, inferred promises and new
text-only checkboxes go to [Capture](../daily-tasks-capture/SKILL.md) as candidates.

Never rank selections, request an execution-order decision, calculate time budgets,
schedule slots, change targets or fit work into a timeframe. Execution order belongs
to the person; planning never authorizes external messages or delegated execution.

## 6. Verify and report

Only `daily_tasks_confirm_plan(session_id, confirmed=True)` after explicit user confirmation
writes updated records, the dated daily plan, the append-only decision log, and fetch cursors.
Preserve completed/cancelled visibility, explicit removals and today's plan identity on repeated
calls. Acceptance alone never authorizes reformatting today's existing file.

For an options screen or planning recap, show the validated `payload.screen` first,
then the saved-plan link and any concise change/error notes. A status-only reply can
lead with the saved-plan link without reprinting the plan. Future tables require an explicit
week-view request.
