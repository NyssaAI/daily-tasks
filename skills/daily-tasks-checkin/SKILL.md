---
name: daily-tasks-checkin
description: Run or resume an anytime personal check-in, reconcile Markdown edits and reported progress, resolve conflicts and candidates, and open or create today's local-day plan with automatic carry-forward.
---

# Anytime check-in

Apply [response conventions](../daily-tasks/references/response-conventions.md)
for review screens and numbered status/progress replies.
Use [planning flow](../daily-tasks/references/planning-flow.md) for the shared
four-hour maintenance worker, current/previous-plan checks and inventory refresh.

Resolve profile via [setup](../daily-tasks-setup/SKILL.md). Read
[operation protocol](../daily-tasks/references/operations.md) and
[CLI](../daily-tasks/references/cli.md). Save compact resumable progress at
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
   time. Apply safe accepted changes through [records](../daily-tasks-records/SKILL.md).
4. Present the small queue of decisions: conflicting edits, new candidates, unclear
   dispositions. Offer explicit batch acceptance where compatible. Save progress after
   each decision; never interpret interruption or silence as acceptance. Allow skipping
   unresolved items while processing independent ones. Do not ask resolved questions again.
5. Open/create today's local-day plan using [daily planning](../daily-tasks-plan/SKILL.md).
   Write it under `<vaultRoot>/<dailyPlansRelative>` from the profile. Only resumable
   progress belongs in stateRoot; the daily Markdown plan must be outside that directory.
   Carry unfinished selections from most recent earlier plan automatically, no skipped-day
   plans, including into a plan pre-created by future selection. Use the dated rollover
   state and pending-operation protocol; file existence is not rollover completion.
   Separate own and delegated saved work; leave execution order to the person.
   Do not require every open task to receive a day allocation. No timeframe fitting.
6. Revalidate affected records, links, closure/reopening effects and views, verify log
   appends, then save baselines. Report plan link, changes applied, and any pending
   conflicts/candidates. A check-in with unresolved items is resumable, not falsely complete.

Task uncheck reopens task and closed parents; unchecking DoD/reopening blocker reopens
closed parents but leaves completed tasks. Invalid parent close requests explain unmet
conditions. Lost time precision uses now and retains reported wording. Completed and
cancelled items remain visible today and don't carry; removed open items stay deselected.
