> [!IMPORTANT] Scope Directive
> This workflow owns running or resuming an anytime personal check-in, reconciling manual Markdown edits against baselines, resolving conflicts and candidates, and coordinating with `records.md` and `plan.md` to update today's local-day plan. It does NOT own vault/profile setup (`setup.md`), candidate extraction rules (`capture.md`), standalone record schemas (`../references/records.md`), or low-level reconciliation theory (owned by `../references/operations.md`).

# Anytime check-in

Reconcile manual Markdown edits, reported progress, and pending operations before opening or updating today's local-day plan. Reference [planning flow](../references/planning-flow.md), [operations](../references/operations.md), [MCP / CLI interface](../references/cli.md), and [response conventions](../references/response-conventions.md) for domain contracts.

## 1. Pre-flight and resumable state

1. **Enforce all four full-setup gates**:
   - Verify live `daily_tasks_*` MCP tools in the current harness, Schema Version 2 `~/.nyssa-ai/daily-tasks/config.json` (`projectsRoot`, `dailyPlansRelative`, `sources`, `user.email`, IANA `timezone`), and vault templates baseline (`~/.nyssa-ai/daily-tasks/templates/updates.json`).
   - If **any** gate fails, **immediately halt** check-in and complete [Setup](setup.md) first; never improvise a prose check-in by manually scraping vault files.
   - Bind one `vault_root`, `projectsRoot`, `dailyPlansRoot`, and `runtime_root` throughout recovery and follow-up turns; never mix inventories or numbered replies across vaults.
2. **Track resumable check-in progress**:
   - Persist compact resumable state at `<runtime_root>/checkin.json` recording the local day, pending operation IDs, unresolved candidate/conflict IDs, processed source versions, and next step.
   - If a check-in spans a midnight rollover, update the target plan date to the new local day while preserving the identity and disposition of unresolved decisions.

## 2. Step-by-step check-in checklist

1. **Recover interrupted operations**:
   - Inspect `<runtime_root>/operations/` for any incomplete write-ahead checkpoints matching the active vault binding ([operations](../references/operations.md)).
   - Verify on-disk file hashes against expected `before`/`after` values and complete unambiguous missing effects before starting new edits.
2. **Reconcile manual Markdown edits and repair malformed files**:
   - Compare project views, task files, and daily plans against their stored per-view baselines in `<runtime_root>/reconciliation.json`.
   - If any malformed or unparseable Markdown files are detected, immediately route them to [Records](records.md) for non-destructive repair while preserving all user notes byte-for-byte.
   - Separate safe independent field deltas from conflicting edits to the same field; suspend only the conflicting records for user adjudication without freezing unrelated items.
   - Preserve missing files or duplicate UUIDs as explicit conflicts rather than silently creating new tasks or deleting records.
3. **Process reported progress and daily source scans**:
   - Distinguish actual execution start (`in-progress`) and completion (`completed`) from assignment or plan selection.
   - Apply reopening rules when tasks, embedded DoD criteria, or preventing blockers are unchecked:
     - Unchecking a task or task DoD criterion reopens that task and its completed parent milestone and project.
     - Unchecking a milestone DoD criterion or reopening a preventing blocker reopens the completed parent milestone and project while leaving completed child tasks unchanged.
   - If `sources.autoScan` is enabled and `<runtime_root>/source-scans/YYYY.MM.DD.json` is absent for today, run the daily scan via [Capture](capture.md).
   - Route quoted requests, inferred promises, and new unlinked checkboxes to [Capture](capture.md) as candidates; apply accepted record updates via [Records](records.md).
4. **Adjudicate conflicts and candidates**:
   - Present a compact decision queue of conflicting edits, new candidates, and ambiguous dispositions, offering batch acceptance where compatible.
   - Save progress to `<runtime_root>/checkin.json` after each user reply; never treat silence or session interruption as acceptance.
   - Allow the user to skip unresolved items while continuing with independent work, and never re-ask already-resolved questions.
5. **Open or update today's daily plan via Plan**:
   - Delegate daily plan opening, rollover (`↺`), message suggestion adjudication, and task selection to [Daily plan](plan.md) using the `daily_tasks_*` MCP tools (`daily_tasks_start_session` with `vault_root?`, `daily_tasks_execute_operations`, `daily_tasks_advance_screen`, `daily_tasks_confirm_plan`).
   - Enforce [Daily plan](plan.md)'s screen gate: display `payload.screen` unchanged and never substitute a prose check-in summary for the validated planning screen.
   - Write the confirmed daily plan strictly under `<vault_root>/<dailyPlansRelative>/YYYY.MM.DD-daily-plan.md` (never inside `<runtime_root>` or `.nyssa-ai/`), keeping `My work`, `Delegated work`, and `Follow-up work` separated without time-slot scheduling.
6. **Finalize baselines and report**:
   - Revalidate modified records, reciprocal links, parent closure/reopening effects, decision-log entries, and `<runtime_root>/reconciliation.json` baselines.
   - Report the clickable daily-plan link, applied record changes, and any remaining unresolved conflicts or candidates (marking a check-in with deferred items as resumable rather than falsely complete).

## Verification

Before reporting check-in completion:
- [ ] Confirm all malformed Markdown files discovered during check-in were repaired via [Records](records.md) without losing user notes.
- [ ] Confirm conflicting manual edits and unaccepted candidates were surfaced for explicit user decision and never silently overwritten or auto-accepted.
- [ ] Confirm `daily-tasks-mcp` was used strictly via `daily_tasks_*` MCP tools and today's daily plan was written under `<vault_root>/<dailyPlansRelative>/`.
- [ ] Confirm `<runtime_root>/decision-log.json`, `<runtime_root>/reconciliation.json`, and `<runtime_root>/checkin.json` reflect the verified on-disk state with zero `.nyssa-ai/` files inside `vault_root`.
