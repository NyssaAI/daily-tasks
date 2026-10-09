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

If enrolling or changing reconciliation baselines, include `baseline` with
`beforeHash`, exact `beforeText` when that hash is non-null, and `value`:
`{schemaVersion:1, records:{UUID:{canonical:{fields}, views:{absolutePath:{hash,
selected?, checked?, state?}}}}}`. Hashes are SHA256 of exact UTF-8 file bytes.
Changes must match declared effects and actual canonical records/view rows.
Preserve unrelated entries. `operation-verify` returns verified, pending or
conflict. `operation-complete` saves the checked JSON baseline and removes the
checkpoint only after effects, sources and exact event match. Inspect the status;
exit zero alone is insufficient. `--dry-run` previews without writing.

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

These checks enforce supported CLI transitions. They cannot authenticate an
agent-authored worker receipt or prevent unrestricted host file tools from
writing state. Report unavailable worker execution accurately.
