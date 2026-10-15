# JavaScript integrity and log interface

> [!IMPORTANT]
> **Scope Directive**: This document is strictly an API, ABI, and invocation specification for `src/cli/daily-tasks.mjs` (and packaged `bin/daily-tasks.mjs`) and related CLI entrypoints. It documents command signatures, input/output schemas, runtime execution invariants, platform/serialization rules, and concrete payload examples. Domain workflows, markdown styling, planning business rules, and user-facing protocols belong exclusively in their respective skill and reference documents.

Requires Node >=22 and permitted filesystem/process access. Resolve `PACKAGE_ROOT` from the installed skill's actual location, never assume a cache path. The canonical source entrypoints are:

```text
node PACKAGE_ROOT/src/cli/daily-tasks.mjs --help
node PACKAGE_ROOT/src/cli/daily-tasks.mjs new-id
node PACKAGE_ROOT/src/cli/daily-tasks.mjs OPERATION --input ABSOLUTE_JSON_FILE
node PACKAGE_ROOT/src/cli/warm-project-index.mjs --vault-root ABSOLUTE_VAULT [--home-root ABSOLUTE_HOME] [--profile-path ABSOLUTE_PROFILE | --configuration-sources JSON] [--state-root ABSOLUTE_STATE] [--dry-run]
```

Packaged portable artifacts retain `bin/daily-tasks.mjs`; Cowork uses `scripts/daily-tasks.mjs`. Write structured input with file tools into the working scope's `.temp/`; do not use interpolated shell JSON. Parse JSON stdout and process exit status; stderr outputs a single JSON error on failure. Exit zero indicates execution completed without process errors, not that validation passed or closure was authorized. Mutations accept `--dry-run` and write nothing to disk.

## Runtime invariants and platform rules

### Host clock and timestamp rules
- Omit `now` from initial `planning-prepare`, `resolve-context`, and `activity-time` so defaults read the actual host clock. Use the returned `localDate` (which may differ from UTC date). Never fabricate an instant from a planning date or fixture.
- A requested planning day is not a clock override; future selections use `plan-selection`'s `date` argument with the actual host date.
- Historical actions belong in `reported`, not `now`. `recorded_at` is always the host time when the entry is recorded.
- Only recovery of an existing operation preserves its original event timestamps.

### Windows and PowerShell JSON safety
- On Windows, preserve JSON timestamps as strings. PowerShell's `ConvertFrom-Json` converts ISO strings into .NET `DateTime` objects, which shifts GMT timestamps or alters formatting when reserialized.
- When available, use `ConvertFrom-Json -DateKind String` for CLI results, checkpoints, and record JSON; otherwise parse using Node.js `JSON.parse`.
- Keep exact `activity_at` and `recorded_at` strings returned by `activity-time`. Do not reparse or convert them to local time.

### Context binding and routing checks
- `resolve-context` returns `planningBinding` (an opaque hash of normalized roots).
- Calls to `planning-review`, `plan-selection`, `carry-forward`, and `plan-rollover` require `contextBinding` from `resolve-context.planningBinding`.
- When inventory is supplied, pass `inventoryBinding` from `project-index.planningBinding`.
- When a numbered review mapping is active, pass `mappingBinding` returned by `planning-review`. Roots are fixed to one workspace context; mismatched roots or foreign inventories fail before producing effects.

## Operations matrix

| Operation | Input | Result/effect |
| --- | --- | --- |
| new-id | none | New UUIDv7; no write |
| activity-time | reported?, now? | activity_at, recorded_at, time_defaulted |
| local-day | time GMT ISO, timezone | local YYYY.MM.DD |
| format-time | time GMT ISO, timezone | Local display with explicit zone |
| validate-profile | profile object | valid/errors/resolvedTimezone; no save |
| resolve-context | absolute workspaceRoot (or vaultRoot) or captured initialCwd for workspace work; homeRoot for personal-only setup; configurationSources?, legacy profilePath?/configRoot?, preferenceOverrides?, stateRoot?, now? | Layered preferences, versioned source selections, provenance/writableScopes, independent absolute roots, identity, actual timezone/localDate, templates and TTL; no writes |
| template-prepare | context inputs above, kinds (nonempty distinct supported kinds), scope? user/project/legacy, review? | Active file/available/upstream content, three-way comparison, placement proposals, pending file updates, policy, offer decision, token and storage hashes; no writes |
| template-state | same context/kinds/scope, expectedToken, action baseline/decide/recover, decisions? (one per kind), originalWords for decide, dryRun? | Retained JSON snapshots and choices; file-update-required until skill-owned Markdown effects are verified by a fresh baseline; project decisions logged exactly once; never writes Markdown |
| planning-prepare | context inputs above; forceRefresh?, page?, allMilestones?, dryRun? | Actual plan identities/hashes, scoped inventory, rollover proposal, review, active dailyPlan/planDayReview template packet, state hashes, pendingOperations names and recovery impacts, maintenance gate, enrollment issues; cache writes only |
| planning-state | context inputs with packet context.now; action save-review/complete-rollover, expectedPlanHash, expectedPreviousHash (null if absent), expectedStateHash (null if absent), expectedInventoryHash; expectedReviewHash and reviewMarkdown for save-review; same page?/allMilestones? as preparation, dryRun? | Re-prepares sources/checkpoint evidence and validates the review draft/mapping or no-change rollover receipt; unrelated recovery permits review saves, affected/unknown recovery blocks the action; rejects invalid screens, stale templates/state, unresolved carry and wrong plan type |
| project-index | vaultRoot, projectsRoot, dailyPlansRoot absolute; timezone; now?, ttlSeconds?, forceRefresh?, dryRun? | rebuilt/reused/preview, path, inventory, read metrics; disposable JSON cache only |
| warm-project-index | dedicated flags: vault-root required; home-root optional; configuration-sources JSON or exclusive profile-path; state-root and dry-run optional | Replays selected sources/null absences and established state, calls project-index without forceRefresh; compact status/counts/metrics only, disposable cache write at most |
| invalidate-project-index | vaultRoot absolute, dryRun? | Invalidates freshness sidecar; no Markdown/state changes |
| planning-review | inventory, userEmail, timezone; now?, selected?, selectedRecords?, mapping?, position?, page?, allMilestones?, pendingFutureIds? | All-owner scoped counts, selected/available rows with ownership metadata, stable mapping, diagnostics; one project per page; page/pageCount, position and reviewComplete; lowest incomplete milestone only (allMilestones does not expand selection) |
| plan-selection | resolved context including stateRoot, inventory and recovery from planning-prepare, taskIds, action add/move/remove, today; date for add/move | Proposed selection transfers/file targets and conflicts, including suspended records and overlapping source/destination plans or dated state; skill writes Markdown |
| maintenance-status | resolved context inputs | Boolean inspectionDue, alwaysCheck; workerEvidence.status unsupported and fullReconcileDue null (not overdue/success); no write |
| maintenance-inspect | resolved context inputs, dryRun? | Actual graph/navigation/baseline checks; saves CLI inspection JSON only; no worker success |
| operation-verify | resolved context inputs, operationPath absolute | Actual effects/protected sources/exact event checks; typed selection intent also reports persistedStatus and pending/conflicting owned state; no write |
| operation-complete | same, dryRun? | Verified baseline save, typed selection removal-history derivation across dates, checkpoint removal last |
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
| carry-forward | rows, records, userEmail; inventory? with today | own/delegated/follow-up/unresolved selection, excludes terminal/future-selected work |
| plan-rollover | today, planId, userEmail; currentRows?, state?, previousDate?, previousRows?, records?, inventory?, removedIds? | due/complete/conflict and merged selected rows with own/delegated/follow-up carry provenance; no writes |
| log-append | projectsRoot, entry, dryRun?; new workspace.migration also requires vaultRoot (or captured initialCwd), profile scope and operationPath | Append decision; migration checks actual retirement against bound checkpoint; identical operation retry deduplicated |
| log-query | projectsRoot, recordId?, action?, since?, until?, limit?, offset? | Matching entries across active/archive files |
| log-archive | projectsRoot, dryRun? | Preserve current file in archives; next append starts new dated segment |

## Concurrency and locking

File operations that modify templates, state, or decision logs acquire an explicit lock directory. If a process stops abruptly, the lock surfaces its path and metadata. Confirm the recorded process has terminated before removing the lock directory during recovery. Never automatically remove or ignore active lock directories.

## Planning-state payload construction

After recovery/reconciliation and plan creation or updates, obtain a fresh `planning-prepare` packet. Assemble `planning-state` inputs directly from packet properties:

```javascript
const shared = {
  vaultRoot: packet.context.vaultRoot,
  ...(packet.context.configurationSources
    ? {configurationSources: packet.context.configurationSources}
    : {profilePath: packet.context.profilePath}),
  stateRoot: packet.context.stateRoot,
  homeRoot: packet.context.homeRoot,
  preferenceOverrides: packet.context.preferenceOverrides,
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
  expectedReviewHash: packet.reviewHash,
  reviewMarkdown: draftedScreenMarkdown
};

const rolloverInput = {
  ...shared,
  action: 'complete-rollover',
  expectedStateHash: packet.state.rollover.sha256
};
```

Serialize the input as JSON in `.temp/` and execute:
```bash
node PACKAGE_ROOT/bin/daily-tasks.mjs planning-state --input ABSOLUTE_JSON_FILE
```

Display the resulting `value.screen.markdown` unchanged. `complete-rollover` is used strictly for an eligible no-change rollover; changes to daily task membership require the full rollover operation flow.

## Decision log input schema

When appending an event using `log-append`, supply the following JSON schema:

```json
{
  "projectsRoot": "/absolute/workspace/1-projects",
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
