# JavaScript integrity and log interface

Requires Node >=22 and permitted filesystem/process access. Resolve PACKAGE_ROOT from
the installed skill's actual location, never assume a cache path. The portable entry is:

```text
node PACKAGE_ROOT/scripts/daily-tasks.mjs --help
node PACKAGE_ROOT/scripts/daily-tasks.mjs new-id
node PACKAGE_ROOT/scripts/daily-tasks.mjs OPERATION --input ABSOLUTE_JSON_FILE
```

For Cowork's generated package the entry is `scripts/daily-tasks.mjs` (same implementation).
Write structured input with file tools into the working scope's `.temp/`; no interpolated
shell JSON. Parse JSON stdout and exit status; stderr is one JSON error on failure.
Exit zero means execution succeeded, not that diagnostics are empty or closure is allowed.
No credentials/environment variables needed. Mutations accept `--dry-run` and write nothing.

For a new request, omit `now` from initial `planning-prepare` / `resolve-context`
and from `activity-time`: their defaults read the actual host clock. Use the
returned localDate; its calendar date can differ from the UTC date. Never invent
an instant from a requested planning day, or copy a clock from records, caches,
examples or fixture files. An override must be a freshly captured host instant or
an explicitly declared full GMT simulation clock for that run, not a date-only
request. Future selections use `plan-selection`'s `date`, with the real `today`;
they do not move the clock forward.
Reuse a preparation packet's context.now only for that packet's state save;
the next request reads the clock again. New decisions use fresh `activity-time`
results for their event and record timestamps. A reported historical activity
belongs in `reported`, not `now`; recorded_at remains the actual recording time.
Maintenance inspection records its own actual GMT completion time and never
advances worker success. Only recovery of an existing operation preserves its original
event timestamps. A new operation must not inherit that recovery event's clock.

On Windows, preserve JSON timestamps as strings. PowerShell's default
`ConvertFrom-Json` can turn ISO strings into `DateTime` objects; later interpolation
or reparsing can shift GMT timestamps or produce culture-specific text. When its
`DateKind` parameter is available, use `ConvertFrom-Json -DateKind String` for CLI
results, checkpoints and record JSON. Otherwise use Node's `JSON.parse` to preserve
strings; do not round-trip this data through PowerShell's default date conversion.
Keep the exact `activity_at` and `recorded_at` strings returned by `activity-time`
in records, checkpoints and log inputs, including retries. Do not reparse them with
`[DateTime]::Parse` or convert them to local time for persistence. Use `format-time`
only for display. Before `log-append`, compare both timestamp strings with the
saved activity-time result; syntactically valid GMT text alone cannot detect a shift.

| Operation | Input | Result/effect |
| --- | --- | --- |
| new-id | none | New UUIDv7; no write |
| activity-time | reported?, now? | activity_at, recorded_at, time_defaulted |
| local-day | time GMT ISO, timezone | local YYYY.MM.DD |
| format-time | time GMT ISO, timezone | Local display with explicit zone |
| validate-profile | profile object | valid/errors/resolvedTimezone; no save |
| resolve-context | absolute vaultRoot or captured initialCwd; homeRoot?, profilePath?, configRoot?, stateRoot?, now? | Resolved absolute roots, identity, actual timezone/localDate, templates and TTL; no writes |
| planning-prepare | context inputs above; forceRefresh?, page?, allMilestones?, dryRun? | Actual plan identities/hashes, scoped inventory, rollover proposal, review, state hashes, pending operations, maintenance gate, enrollment issues; cache writes only |
| planning-state | context inputs with packet context.now; action save-review/complete-rollover, expectedPlanHash, expectedPreviousHash (null if absent), expectedStateHash (null if absent), expectedInventoryHash; expectedReviewHash for save-review; same page?/allMilestones? as preparation, dryRun? | Re-prepares and checks sources, then atomically saves derived review mapping or a no-change rollover receipt; rejects pending carry/operations, wrong plan type, stale state |
| project-index | vaultRoot, projectsRoot, dailyPlansRoot absolute; timezone; now?, ttlSeconds?, forceRefresh?, dryRun? | rebuilt/reused/preview, path, inventory, read metrics; disposable JSON cache only |
| invalidate-project-index | vaultRoot absolute, dryRun? | Invalidates freshness sidecar; no Markdown/state changes |
| planning-review | inventory, userEmail, timezone; now?, selected?, selectedRecords?, mapping?, page?, allMilestones?, pendingFutureIds? | Owner-focused counts, selected/available rows, stable mapping, diagnostics; max 15 addition rows |
| plan-selection | inventory, taskIds, action add/move/remove, today, dailyPlansRoot; date for add/move | Proposed selection transfers/file targets and conflicts; skill writes Markdown |
| maintenance-status | resolved context inputs | Separate inspection freshness and unavailable trusted worker evidence; no write |
| maintenance-inspect | resolved context inputs, dryRun? | Actual graph/navigation/baseline checks; saves CLI inspection JSON only; no worker success |
| operation-verify | resolved context inputs, operationPath absolute | Actual effects/protected sources/exact event checks; no write |
| operation-complete | same, dryRun? | Verified baseline save and checkpoint removal |
| rollover-complete | same, schemaV2 rollover checkpoint | Recomputed selections and identity checks before receipt/baseline/checkpoint completion |
| migration-retirement | same, schemaV2 migration checkpoint | Pre-removal content and live incoming-reference checks; allowed/ issues; no deletion |
| migration-complete | same, retained source snapshot, dryRun? | Post-removal effect/event/baseline checks; no chronological attestation |
| inspect-navigation | projectsRoot absolute, dailyPlansRoot? | Local identity, heading and attachment diagnostics; no write |
| next-record-number | projectsRoot absolute, type milestone/task/blocker, parentId | Next unused parent-local label from live records and queried retirement history; number:null on ambiguity; no reservation |
| parse-record | markdown, path? | Structured record; no write |
| parse-checklist | markdown | Rows with ref IDs or candidate indication |
| inspect-records | projectsRoot absolute | Canonical records and integrity diagnostics; ignores dot folders, rejects symlinks |
| validate-records | records | Metadata/identity diagnostics |
| check-links | records | Identity, path and reciprocal link diagnostics |
| check-closure | recordId, records | allowed/reasons; no state transition |
| reconcile-record | base, current, views | Proposed record, conflicts and changes; no write |
| reopen-ancestors | records, changedIds | Proposed records and changedIds; no write |
| recover-operation | operation:{changes:[{key,before,after}]}, actual:{key:value} | pending/already-applied/conflict |
| carry-forward | rows, records, userEmail; inventory? with today | own/delegated/unresolved selection, excludes terminal/future-selected work |
| plan-rollover | today, planId, userEmail; currentRows?, state?, previousDate?, previousRows?, records?, inventory?, removedIds? | due/complete/conflict and merged selected rows with carry provenance; no writes |
| log-append | projectsRoot, entry, dryRun?; new workspace.migration also requires vaultRoot (or captured initialCwd), profile scope and operationPath | Append decision; migration checks actual retirement against bound checkpoint; identical operation retry deduplicated |
| log-query | projectsRoot, recordId?, action?, since?, until?, limit?, offset? | Matching entries across active/archive files |
| log-archive | projectsRoot, dryRun? | Preserve current file in archives; next append starts new dated segment |

Log entry: id and operation_id UUIDv7; action string; record_ids array (empty for profile
decisions); actor `{kind:"person"|"agent",id:email-or-agent-name}`; activity_at and
recorded_at GMT ISO; time_defaulted boolean; optional original_words, before, after,
corrects prior entry ID. Use original_words/reason in after when necessary to retain
decision context; avoid copying entire private source messages. A person actor must be
an email. Log validates structure, not real-world authentication or user acceptance.

Append-only means existing entries never change: corrections reference earlier entries.
Active file is replaced atomically to extend its JSON array; logical history is append-only.
Archive rotation preserves old file bytes and ID reservation. Query includes archives,
limit defaults 100 and max 1000; filters since/until on recorded_at. Reads scan history
linearly in v1; archive avoids rewriting all past history on every active-file append.
No automatic retention deletion. Explicit `log-archive` is the supported performance knob.

Timezone inputs accept an explicit IANA zone or `"system"`. The latter resolves
the executing host's runtime default zone. New profiles use `"system"`; validation
returns the detected zone as `resolvedTimezone` without changing the profile.
Date/time rendering uses the actual zone name. Detection failures are errors,
requiring an explicit override rather than an assumed UTC zone.

Planning CLI calls (`planning-review`, `plan-selection`, `carry-forward`,
`plan-rollover`) require vaultRoot/projectsRoot/dailyPlansRoot and contextBinding
from resolve-context's planningBinding. With inventory also pass inventoryBinding
from project-index's planningBinding. With a nonempty numbered mapping pass its
mappingBinding, returned by planning-review. Roots are one fixed vault context;
wrong roots, another inventory or another numbered screen are errors before effects.
Pure library derivations can run without routing tokens; they do not constitute a
host planning session or authority to write Markdown.

Inventory shape is schemaVersion/generatedAt/scope/projects/milestones/tasks/
blockers/sources/diagnostics. Each open task's planned array has zero or one active
{date,source} entry. Conflicting dates remain in diagnostics, never arbitrarily
collapsed. Scope/source paths are portable; full instructions remain in records.
An independent external projects root uses the logical `@projectsRoot` scope anchor.
Resolve it only from the current context. The result's planningBinding is runtime
routing evidence outside the agreed inventory file shape; actual root compatibility
remains fingerprinted in its disposable freshness sidecar.
Counts, lateness, eligibility and first incomplete milestone are computed on read.
Refresh hashes on rebuild; reuse checks source membership/metadata. The sidecar
is derived freshness evidence, not authoritative state. See [planning flow](planning-flow.md).

Concurrency uses a lock. A stale lock is surfaced with its path; confirm the recorded
process is stopped before removing only that lock directory through deliberate recovery.
Never automatically break a lock based on age. Corrupt JSON is an error, not an empty log.
Keep the pending operation and return the exact error; don't edit log files to make it pass.

## Planning-state input from a preparation packet

After recovery/reconciliation and any plan creation or writes, obtain a fresh
`planning-prepare` packet. Preserve the same `page` and `allMilestones` options.
The following input construction uses values returned by that actual packet; do
not substitute sample hashes or invent a clock. `prepareOptions` is the input
used for that preparation, and `packet` is its parsed JSON result.

```javascript
const shared = {
  vaultRoot: packet.context.vaultRoot,
  profilePath: packet.context.profilePath,
  configRoot: packet.context.configRoot,
  stateRoot: packet.context.stateRoot,
  homeRoot: packet.context.homeRoot,
  now: packet.context.now,
  page: prepareOptions.page,
  allMilestones: prepareOptions.allMilestones,
  expectedPlanHash: packet.current.sha256,
  expectedPreviousHash: packet.previous?.sha256 ?? null,
  expectedInventoryHash: packet.inventoryHash
};
const reviewInput = {
  ...shared,
  action: 'save-review',
  expectedStateHash: packet.state.review.sha256,
  expectedReviewHash: packet.reviewHash
};
const rolloverInput = {
  ...shared,
  action: 'complete-rollover',
  expectedStateHash: packet.state.rollover.sha256
};
```

Serialize the chosen input as JSON with file tools in the working scope's `.temp/`,
then invoke `node PACKAGE_ROOT/scripts/daily-tasks.mjs planning-state --input ABSOLUTE_JSON_FILE`.
`undefined` options are omitted by JSON serialization; explicit options must match
preparation. These are alternative inputs, not a sequence using one stale packet.
Reprepare after a state or source write before constructing another input.
`complete-rollover` is only for an eligible no-change rollover. Pending membership
changes require the [rollover operation protocol](planning-flow.md#once-per-day-rollover).
A rejected hash or failed state save remains pending; never report it complete.

This construction was exercised using an actual synthetic preparation packet:
review saving and a no-change receipt succeeded, and stale state was rejected.
It documents input assembly, not a replacement planning orchestrator.

## Illustrative log input (use generated IDs and actual timestamps)

```json
{
  "projectsRoot": "/absolute/vault/1-projects",
  "entry": {
    "id": "019a1234-5678-7abc-8def-0123456789ab",
    "operation_id": "019a1234-5678-7abc-8def-0123456789ac",
    "action": "task.accepted",
    "record_ids": ["019a1234-5678-7abc-8def-0123456789ad"],
    "actor": {"kind": "person", "id": "user@example.com"},
    "activity_at": "2026-10-05T16:30:00.000Z",
    "recorded_at": "2026-10-05T16:30:00.000Z",
    "time_defaulted": false,
    "original_words": "Accept this task",
    "after": {"task-state": "not-started"}
  }
}
```
