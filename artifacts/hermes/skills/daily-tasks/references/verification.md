# Verified operation completion

Use resolved context inputs and an absolute `operationPath` under the resolved
state root's `operations/UUID.json`. The skill authors Markdown and checkpoints;
the CLI reads actual files and queries the exact event through the log API.
Caller-supplied `actual` or `verified` assertions are not completion evidence.

New checkpoints use `schemaVersion: 2`, `operation_id` (UUIDv7), the exact
`contextBinding` from preparation, `event` (the log payload), and `files`:
`[{path: absolute, before: SHA256-or-null, after: SHA256-or-null}]`. Null means
absence. Optional `protectedFiles: [{path, sha256}]` bind unchanged sources.
Paths must be visible files in the resolved projects or daily-plan roots;
symlinks and state/log files cannot be effects. Keep recoverable before bytes
in project `.temp/`. Legacy checkpoints remain pending until their original
evidence has been recovered; changing a version number does not supply evidence.
Schema-v2 completion rejects legacy `changes` arrays rather than ignoring their
unverified effects.

If enrolling or changing reconciliation baselines, include `baseline` with
`beforeHash`, exact `beforeText` when that hash is non-null, and `value`:
`{schemaVersion:1, records:{UUID:{canonical:{fields}, views:{absolutePath:{hash,
selected?, checked?, state?}}}}}`. Hashes are SHA256 of exact UTF-8 file bytes.
Changes must match declared effects and actual canonical records/view rows.
Preserve unrelated entries. `operation-verify` returns verified, pending or
conflict. `operation-complete` saves the checked JSON baseline and removes the
checkpoint only after effects, sources and exact event match. Inspect the status;
exit zero alone is insufficient. `--dry-run` previews without writing.

## Selection removal history

For accepted selection adds, removals or moves, use `operation-complete` with a
narrow `selectionState` intent, not `rollover-complete` or planning-state's
no-change rollover action. Do not relabel a legacy `changes` checkpoint as v2.
Declare `selectionState: {direction: "add" | "remove" | "move", taskIds: [UUID],
source?, destination?}`. Remove requires only source, add only destination, move
both (distinct dates and plan UUIDs). Every task ID is explicit and unique.

Each source/destination is `{date, planPath, planId, beforeMarkdown,
stateBeforeHash, stateBeforeText}`. Dates are `YYYY.MM.DD`; planPath is exactly
`dailyPlansRoot/YYYY.MM.DD-daily-plan.md`. Preserve existing plan identity and
creation time. beforeMarkdown is exact UTF-8 before text matching its file effect,
or explicit null for a new destination. State beforeText proves stateBeforeHash;
both are explicitly null when the dated rollover file did not exist. Do not
supply an after-state object or a caller-selected state path. The only declared
file effects are these plans; include protected canonical task paths/hashes and
unchanged historical/project files that must survive. Bind the original event
ID/payload, `action: selection-add/selection-remove/selection-move`, record_ids
matching taskIds, and `before:{date:source date or null}` /
`after:{date:destination date or null}`. Preserve all original actor/timing/words.

Include the supported `baseline` proposal above, retaining canonical and unrelated
entries/views. For each intended task, affected views carry the exact after hash
and selected:true at destination, selected:false at source (or omit the removed
source view). The CLI checks actual membership and rejects unrelated membership
changes or duplicate references, even if their bytes match the declared after hash.

The CLI derives source removal history by adding only taskIds and destination
history by clearing only taskIds, preserving other IDs and all existing receipt
fields. Missing state becomes `{schemaVersion:1,date,planId,removedIds}` without
operationId/completedAt: a selection change never proves rollover completed.
Paths are derived only beneath `stateRoot/rollover`. All affected state and the
baseline are checked before any write, accepting only exact before bytes/absence
or the exact derived after bytes (two-space JSON plus final newline). Unexpected
edits return conflict. Matching already-applied state is not rewritten.

For this intent, `operation-verify` also reports `persistedStatus` for Markdown,
protected sources and the exact event, plus `ownedState.pending/conflicts`.
Overall pending may mean only owned state remains even when persistedStatus is
verified. `operation-complete` then atomically/optimistically writes remaining
owned JSON, rechecks evidence and deletes the checkpoint last. A partial failure
retains it; retry with the same checkpoint resumes only remaining state. Neither
command authors Markdown or appends the event. Inspect status, not just exit code.

Changed rollover uses `rollover-complete` and adds `rollover` with `date`,
`planId`, `previousPlanId`, `expectedCreatedAt`, `removedIds`,
`expectedSelectedIds`, `previousPath`, `previousHash`, `expectedStateHash` (hash
of the dated state before the checkpoint, null if absent), and
`sourceSnapshot:{currentMarkdown, taskSources:[{path,sha256}]}`. A newly created
plan uses `currentMarkdown:null` and a declared null-before effect. Existing plan
identity and creation time are preserved. The CLI recomputes selection/carry
facts from actual records and checks the nearest actual earlier plan before saving
its receipt. When no earlier plan exists, previousPath, previousHash and previousPlanId
are explicitly null. Recovery may finish an older dated checkpoint with the current
clock; it retains original event timestamps and the dated receipt's removal history.

Migration adds `migration` with `retiringPath`, `destinationPath`, `sourceHash`,
`expectedCriteria` and `preservedFields`. Run `migration-retirement` while the
source still exists, immediately before skill-owned removal; `allowed:false`
keeps it pending. Retain exact retiring bytes as
`sourceSnapshot.retiringMarkdown` on the operation. `migration-complete` checks
declared absence, destination preservation, remaining live incoming references,
event and baseline. Only a proven absent retiring DoD identity may be removed from
its baseline; unrelated entries remain preserved. It cannot retrospectively attest
that inspection preceded deletion. Neither command deletes Markdown.
For a new `workspace.migration` event, `log-append` requires the same resolved
profile/vault scope, `projectsRoot` and `operationPath`. It checks the exact bound
event, actual post-retirement preservation/references, declared after hashes and
protected sources before writing the log. An identical recorded event remains an
idempotent retry after its checkpoint is cleared. This check cannot prove the
chronological order of the earlier inspection and deletion.

These checks enforce supported CLI transitions. They cannot authenticate an
agent-authored worker receipt or prevent unrestricted host file tools from
writing state. Report unavailable worker execution accurately.
