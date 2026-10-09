---
name: daily-tasks-checkin
description: Run or resume an anytime personal check-in, reconcile Markdown edits and reported progress, resolve conflicts and candidates, and open or create today's local-day plan with carry-forward. Use when asked to check in, resume an interrupted check-in, reconcile manual edits, or review progress across work; apply accepted record changes through Records and daily selections through Plan.
---

# Anytime check-in

Resolve and reuse the existing profile/context using [Setup](../daily-tasks-setup/SKILL.md)
when settings are unresolved or explicitly changed; configured users need no repeated
setup. Load [planning flow](../daily-tasks/references/planning-flow.md) when preparing
context/inventory and checking requested-use maintenance. Bind one vault, projects
root and daily-plan root throughout recovery and follow-up replies; shared personal
preferences never combine vault inventories/state. No router load is required.

Load [operations](../daily-tasks/references/operations.md) before reconciliation,
recovery or consequential writes, [CLI](../daily-tasks/references/cli.md) when invoking
operations, and [response conventions](../daily-tasks/references/response-conventions.md)
before review screens/numbered replies. Save compact resumable progress at
stateRoot/checkin.json: local day, pending operation IDs, unresolved candidate/conflict
IDs, processed source versions and next step. A new day changes plan target, not the
identity or disposition of unresolved decisions.

1. Recover pending operations using expected before/after values, `recover-operation`
   and `log-query`; finish unambiguous missing effects, never duplicate an event.
2. Inspect relevant project/daily views and definitions against per-view baselines.
   Run record/link validation, compare changed fields with `reconcile-record`, and
   separate conflicts from safe deltas. Only affected items wait. Preserve missing
   files/duplicate IDs and their references for explicit resolution. No global freeze.
3. Capture progress reports: distinguish actual start/completion from assignment,
   enforce explicit creation acceptance and owner authority, keep activity and record
   time. A direct instruction to create named work can supply acceptance; quoted
   requests, inferred promises and new text-only checkboxes go to
   [Capture](../daily-tasks-capture/SKILL.md) as candidates. Apply safe accepted changes
   through [Records](../daily-tasks-records/SKILL.md).
4. Present the small queue of decisions: conflicting edits, new candidates, unclear
   dispositions. Offer explicit batch acceptance where compatible. Save progress after
   each decision; never interpret interruption or silence as acceptance. Allow skipping
   unresolved items while processing independent ones. Do not ask resolved questions again.
5. Open/create today's local-day plan using [daily planning](../daily-tasks-plan/SKILL.md).
   Write it under `<vaultRoot>/<dailyPlansRelative>` from the profile. Only resumable
   progress belongs in stateRoot; the daily Markdown plan must be outside that directory.
   Follow Plan's ordered recovery, rollover and review-save checkpoints, including
   carry into pre-created plans and the distinct no-change receipt path. Reprepare
   after writes invalidate packet hashes. An existing file proves neither rollover
   nor successful check-in. Separate personal/delegated saved work; leave execution
   order to the person. No requirement to allocate every task; no timeframe fitting.
6. Revalidate affected records, links, closure/reopening effects and views, verify log
   appends, then save baselines. Report plan link, changes applied, and any pending
   conflicts/candidates. A check-in with unresolved items is resumable, not falsely complete.

Task uncheck or task-DoD uncheck reopens that task and closed parents; unchecking
milestone DoD/reopening blocker reopens closed parents but leaves completed tasks.
Invalid task or parent close requests explain unmet
conditions. Lost time precision uses now and retains reported wording. Completed and
cancelled items remain visible today and don't carry; removed open items stay deselected.
