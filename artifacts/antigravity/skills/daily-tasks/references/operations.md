# Applying and reconciling changes

The skill owns Markdown writes. JS does not own task CRUD.

Keep the active vault/projects/daily-plan binding fixed. Validate checkpoint paths
against that context before recovery or writes: canonical/project views belong to
its projectsRoot, daily views to its dailyPlansRoot, and operating state to its
stateRoot. A checkpoint for another binding is suspended for a separate vault
session; never widen the active roots or search another vault to make an ID resolve.
Include the context planningBinding in new checkpoints and resumable screen state.
For legacy checkpoints without it, verify their explicit paths/identities before
enrollment; absence is not permission to cross vaults.

Load this protocol before consequential Markdown writes or recovery. When applying
status changes, write canonical tasks and required parent effects, then project
views, and only then daily-plan projections. If a project effect fails, preserve
the daily projection and retain the checkpoint; never report a completed batch.
Load [Records](../../daily-tasks-records/SKILL.md) before ownership, lifecycle or
closure/reopening changes. Planning receipts/mappings follow
[planning flow](planning-flow.md); they never replace a changed-Markdown transaction.

For a consequential change:

1. Read relevant records and stored per-view baselines in stateRoot/reconciliation.json.
   Validate identities/metadata/links using the CLI. Surface duplicate/missing records;
   preserve their references and continue unrelated items. New unidentified checkboxes
   become capture candidates, not records with fabricated IDs.
2. Establish user acceptance/authority where required. Build an operation with UUIDv7
   operation_id and event id; exact affected file paths, before/after content hashes,
   intended field changes, actor and timing. Save this pending operation under
   stateRoot/operations/<operation-id>.json BEFORE any Markdown write. This is a
   recoverable pending action, not a second decision log. Preserve original words,
   reason, acceptance source and existing event ID/times across retries.
3. Compare expected before values with actual values immediately before each write.
   Re-read the file if it changed. Merge independent edits or suspend that item on
   conflict; don't use modification time as a winner. Write only the agreed delta,
   retaining prose and unrelated fields. Validate the proposed/actual records.
4. Append the corresponding decision through `log-append`. A retry uses exactly the
   same event and operation IDs/payload. Never directly inspect or patch the log;
   `log-query` verifies whether the operation was recorded. A failure leaves the
   checkpoint pending, not a false success.
   Compare the queried event's entire payload with the checkpoint's saved event;
   matching operation/event IDs alone do not prove the intended decision was logged.
   A differing payload is a conflict and must not advance baselines or completion.
5. Refresh affected views AFTER reconciliation; preserve cancelled/completed daily
   rows for the day. Update per-view snapshots to the exact rendered field values
   and source values. Mark/remove the completed pending checkpoint only after records,
   views, baselines and log append are verified. Checkpoints aren't retained history.

Minimal reconciliation state keyed by record UUID contains canonical field baseline,
each projection path's last-rendered field values, and exact file fingerprints for
optimistic checks. Store only needed fields/hashes, not hidden competing task definitions.
Do not invent a baseline for existing divergent files: initial enrollment reads both,
asks about differences, then establishes it. For a stale view compare against THAT
view's own prior snapshot. Normalize each changed view delta against common canonical
baseline before calling `reconcile-record`; unchanged stale values contribute no edit.
This prevents a stale unchecked box reopening a completed task unintentionally.

Persist field effects as `{key,before,after}` where before/after are presence snapshots:
`{"present":false}` means absent and `{"present":true,"value":...}` means present.
The reconcile CLI returns this encoding with `field`; map field to the checkpoint's
unique key. Actual recovery values remain a plain object. Do not serialize JavaScript
undefined or conflate absence with null. A partial view can explicitly clear optional
assignee/target/start/resolution fields with null; omitted view fields mean no proposed edit.

For safe changes to different fields, retain both. Incompatible edits to the same
field preserve both values and become a durable pending conflict. Continue other
items; never refresh the conflicting representation away or call the check-in fully
reconciled while conflicts remain. Choosing a winner is an explicit supplied decision.

Recovery examines existing checkpoints first at check-in. `recover-operation`
classifies field-level effects as pending, already-applied or conflict. Supplement
with file hashes and `log-query` before applying. Finish missing unambiguous effects
with the original operation/event IDs; do not replay already-applied effects. Unexpected
edits remain conflicts. A missing file is not implied deletion authorization. Preserve
the unresolved pointer until explicit restore/cancel/move resolution. Log script lock
or corruption errors require its documented recovery, never hand-edit its JSON.

Shared files can be changed by multiple actors. JS validation is not a distributed
transaction or authentication boundary. Keep operations short, re-read before writes,
and surface races; don't claim conflict-free background multi-agent editing.
