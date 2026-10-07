# JavaScript integrity and log interface

Requires Node >=22 and permitted filesystem/process access. Resolve PACKAGE_ROOT from
the installed skill's actual location, never assume a cache path. The portable entry is:

```text
node PACKAGE_ROOT/bin/daily-tasks.mjs --help
node PACKAGE_ROOT/bin/daily-tasks.mjs new-id
node PACKAGE_ROOT/bin/daily-tasks.mjs OPERATION --input ABSOLUTE_JSON_FILE
```

For Cowork's generated package the entry is `scripts/daily-tasks.mjs` (same implementation).
Write structured input with file tools into the working scope's `.temp/`; no interpolated
shell JSON. Parse JSON stdout and exit status; stderr is one JSON error on failure.
Exit zero means execution succeeded, not that diagnostics are empty or closure is allowed.
No credentials/environment variables needed. Mutations accept `--dry-run` and write nothing.

| Operation | Input | Result/effect |
| --- | --- | --- |
| new-id | none | New UUIDv7; no write |
| activity-time | reported?, now? | activity_at, recorded_at, time_defaulted |
| local-day | time GMT ISO, timezone | local YYYY.MM.DD |
| format-time | time GMT ISO, timezone | Local display with explicit zone |
| validate-profile | profile object | valid/errors/resolvedTimezone; no save |
| resolve-context | absolute vaultRoot or captured initialCwd; homeRoot?, profilePath?, configRoot?, stateRoot?, now? | Resolved absolute roots, identity, actual timezone/localDate, templates and TTL; no writes |
| planning-prepare | context inputs above; forceRefresh?, page?, allMilestones?, dryRun? | Actual plan identities/hashes, scoped inventory, rollover proposal, review, state hashes, pending operations, maintenance gate, enrollment issues; cache writes only |
| planning-state | context inputs; action save-review/complete-rollover, expectedPlanHash, expectedPreviousHash (null if absent), expectedStateHash (null if absent); page?, allMilestones?, dryRun? | Re-prepares and checks sources, then atomically saves derived review mapping or a no-change rollover receipt; rejects pending carry/operations, wrong plan type, stale state |
| project-index | vaultRoot, projectsRoot, dailyPlansRoot absolute; timezone; now?, ttlSeconds?, forceRefresh?, dryRun? | rebuilt/reused/preview, path, inventory, read metrics; disposable JSON cache only |
| invalidate-project-index | vaultRoot absolute, dryRun? | Invalidates freshness sidecar; no Markdown/state changes |
| planning-review | inventory, userEmail, timezone; now?, selected?, selectedRecords?, mapping?, page?, allMilestones?, pendingFutureIds? | Owner-focused counts, selected/available rows, stable mapping, diagnostics; max 15 addition rows |
| plan-selection | inventory, taskIds, action add/move/remove, today, dailyPlansRoot; date for add/move | Proposed selection transfers/file targets and conflicts; skill writes Markdown |
| maintenance-status | now?, lastFullReconcileAt? | Four-hour reconciliation gate; no worker launch/write |
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
| log-append | projectsRoot, entry, dryRun? | Append decision, identical operation retry deduplicated |
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

## Illustrative input (use generated IDs and actual timestamps)

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
