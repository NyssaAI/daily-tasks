# Executable boundary, v1

ESM Node >=22, no dependencies. Entry `node bin/daily-tasks.mjs <operation> --input <absolute-json-file>`.
Reads structured JSON. One JSON value on stdout, failures JSON `{error,code}` on stderr
and nonzero exit. `--help`; every mutating command supports truthful `--dry-run`.
Project scope is explicit absolute input `projectsRoot`; configuration `configRoot`,
vault `vaultRoot`. Never infer from cwd. CLI resolves no user credentials.

## Shared contracts for implementation units

`lib/identity/identity.mjs`: uuid7(nowMillis?), isUuid7(value).

Log module `lib/log/decision-log.mjs`: async appendDecision(input), queryDecisions(input),
archiveDecisions(input). Input `projectsRoot`, `dryRun?`; append `entry` fields:
`id` UUIDv7, `operation_id` UUIDv7, `action` string, `record_ids` UUIDv7 array,
`actor` {kind:'person'|'agent',id:string}, `activity_at` GMT ISO, `recorded_at` GMT ISO,
`time_defaulted` boolean, `original_words` optional string, `before` optional JSON,
`after` optional JSON, `corrects` optional prior entry UUIDv7. Missing id/times may
be supplied by caller helper, never invent actor/acceptance. Same operation ID retries
must not duplicate; conflicting reuse errors. Query filters `recordId`, `action`,
`since`, `until`, bounded `limit`/`offset`, archives included. Archive rotates current
file preserving old bytes and ID uniqueness; no destructive pruning. Lock serialize
processes, detect corruption, atomic replacement/safe recovery, explicit dry-run.

Integrity module `lib/records/records.mjs`: parseRecord(markdown, path?),
validateRecords(records), checkClosure(recordId, records), checkLinks(records).
Record object `{id,type,path,title,owner,assignee?,state,created_at,updated_at,
started_at?,resolved_at?,target_date?,project_id?,milestone_id?,depends_on:[],
blocks:[],blocked_by:[],criteria:[],refs:[]}`; types project/milestone/task/blocker/dod.
Frontmatter key for state `${type}-state` except DoD criteria booleans from checkboxes.
New task/milestone records use scalar `record_version: 2` (parsed as string `"2"`).
Their own `Definition of Done` section supplies `criteria`; `dod_section: true` is
derived by parsing. Criteria are list checkboxes with hidden unique ID comments;
subheadings remain within the section until a same/higher-level heading ends it.
Criterion evidence links are navigation, not managed task refs. Standalone `dod`
records remain readable for migration. Mixed embedded/standalone milestone DoD blocks
closure. Missing/empty version-2 DoD cannot pass closure. Legacy tasks without DoD
retain old completion semantics until converted. Unknown record versions are invalid.
Number collisions within a parent are identity-independent `invalid-number` diagnostics.
New numbered filenames also allow detection when record metadata is malformed.
Both inventory and inspect-records exclude milestone inputs/outputs holding directories,
including task-shaped attachments; these files are not live task records.
ID comes from scalar frontmatter `id`; legacy `<!-- id: UUID -->` remains readable
and must agree if both are present. Record relations supplied by wiki link + hidden ref
in named sections; YAML metadata uses scalar fields (JSON-quoted strings supported),
links outside metadata. Criteria each `{id,text,checked}`. Missing UUID never synthesized.
Validator returns diagnostic array `{code,recordId?,path?,message}`; does not mutate.
`noncanonical-filename` recommends lowercase descriptive names and `.md` without
silently renaming or invalidating records. Both scans discover legacy `.MD` files.
The shared `recordIssueIsInvalid` classifier treats malformed structured facts
uniformly. Inventory retains invalid ancestor scope as `invalid-planning-scope`
diagnostics, so filtering an invalid milestone cannot expose later work.
Closure returns `{allowed,reasons}`. Dependencies never gate task start. Invalid or
missing relationships affecting closure must prevent affirmative closure.

Reconciliation module `lib/reconciliation/reconciliation.mjs`: pure
`reconcileRecord(base, current, views)` -> `{record,conflicts,changes}`; views are
partial record objects keyed by id, with optional `checked` translated to state.
Only explicit changed values compared against baseline; stale unchanged views don't
override current; independent field changes merge, incompatible same-field edits conflict.
Duplicate/missing identity surfaced by validator before reconcile. Pure
`reopenAncestors(records, changedIds)` -> updated cloned records and changed IDs; preserve
completed task facts when milestone DoD/blockers reopen parents. Unsatisfied task DoD
reopens its owning completed task with start-aware state and clears current resolution,
then reopens completed parents. Cancelled records require explicit reopening decisions.
Do not write documents. Operation recovery plans rely on expected before/after values:
`recoverOperation(operation, actual)` -> report safe pending/already-applied/conflict,
never infer missing user intent.

Reconciliation change values and recovery before/after use JSON-safe snapshots:
`{present:false}` or `{present:true,value:...}`. Recovery keys are unique strings;
actual is plain key->value object with absent keys omitted. Views use null to request
removal of optional assignee/started_at/resolved_at/target_date fields; missing view
fields propose nothing. Do not use undefined in persisted checkpoint payloads.

Time module `lib/time/time.mjs`: `activityTime(reported, now?)` ->
`{activity_at,recorded_at,time_defaulted}`; reject malformed precise timestamps;
missing/ambiguous natural language falls back to now (caller preserves words).
`localDay(iso,timezone)` -> YYYY.MM.DD, `displayTime(iso,timezone)` always names zone.
Parse GMT via strict ISO UTC validation; no implicit local parsing.

`resolve-context` resolves portable ./ and ~/ settings against explicit vault/home
bindings and returns absolute roots, timezone and local day. It never reads subprocess
cwd. Vault profiles precede home profiles; explicit pointers win. Operational state
is separate from home preferences.
It returns `planningBinding`, a fingerprint of the single vault, assigned projects
and daily-plan roots. `planningBinding(input)` and `assertPlanningScope(input)`
are exported from the context module. The fingerprint detects accidental scope
mixing; it is not a filesystem permission or authentication boundary.

`project-index` rebuilds/reuses derived JSON at vaultRoot/.temp/daily-tasks/project-index.json.
`invalidate-project-index` invalidates its separate freshness sidecar. Both support
dry-run and never write Markdown. Metadata/membership checks run before reuse;
hashes refresh during rebuild. Cache JSON is written atomically.
An external assigned projects root uses `@projectsRoot` in portable cache scope.
Operation results carry `planningBinding` separately from inventory JSON.

`planning-review` computes owner-focused counts/options and stable pages of at most
15 additions. `plan-selection` returns explicit add/move/remove effects; the skill
creates dated plans and applies transfers through checkpoints/logging.
CLI `planning-review`, `plan-selection`, `carry-forward` and `plan-rollover` require
the resolved vaultRoot/projectsRoot/dailyPlansRoot and `contextBinding`. With an
inventory, supply its result binding as `inventoryBinding`; with an existing
nonempty numbered mapping, supply `mappingBinding`. Root or binding mismatches
fail before planning. Review results retain the mapping binding. Pure
library helpers do not establish host sessions or authorize Markdown writes.
`maintenance-status` separates four-hour CLI inspection freshness from worker
execution evidence. No trusted host worker adapter is supplied, so worker success
remains unrecorded. `maintenance-inspect` checks actual files, navigation, baselines
and pending operations and saves only `maintenance-inspection.json` with its own
clock. It never changes worker-success timestamps.

SchemaV2 completion checkpoints bind exact file hashes, context, protected sources
and log payloads. `operation-verify` reads actual effects and queries the event;
`operation-complete` saves checked baselines and clears checkpoints. Specialized
`rollover-complete`, `migration-retirement` and `migration-complete` add selection,
identity and retirement-preservation checks. See the canonical
[verification contract](../skills/daily-tasks/references/verification.md).
New `workspace.migration` log appends require resolved profile/vault scope and a
bound `operationPath`; actual retirement, preservation, references and declared
effects must be verified before the event is persisted. Exact recorded retries
remain idempotent after checkpoint clearance.
`inspect-navigation` checks local headings and attachments. `next-record-number`
queries retirement history through the log API and fails closed on ambiguous
labels. Supported scans exclude hidden log directories; unrestricted host file
tools remain outside the CLI's enforcement boundary.

`plan-rollover` is pure: input today, planId, userEmail, optional currentRows/state,
previousDate/previousRows/records/inventory and explicit removedIds. It returns
due/complete/conflict, selected (merged rows), own/delegated carry additions and
unresolved rows. It never writes a plan or completion receipt. The skill owns the
dated stateRoot/rollover receipt and checkpointed Markdown/log/baseline effects.

Checklist and canonical-view parsers share reference association and cancellation
semantics: immediately adjacent comment-only references are accepted, conflicting
IDs are invalid, and legacy unchecked strikethrough Cancelled rows carry explicit
cancelled state. Reconciliation compares that state to the stored baseline; it
does not blindly reapply an unchanged stale cancellation over a reopened task.
