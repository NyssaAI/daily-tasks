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
ID comes from `<!-- id: UUID -->`; record relations supplied by wiki link + hidden ref
in named sections; YAML metadata uses scalar fields (JSON-quoted strings supported),
links outside metadata. Criteria each `{id,text,checked}`. Missing UUID never synthesized.
Validator returns diagnostic array `{code,recordId?,path?,message}`; does not mutate.
Closure returns `{allowed,reasons}`. Dependencies never gate task start. Invalid or
missing relationships affecting closure must prevent affirmative closure.

Reconciliation module `lib/reconciliation/reconciliation.mjs`: pure
`reconcileRecord(base, current, views)` -> `{record,conflicts,changes}`; views are
partial record objects keyed by id, with optional `checked` translated to state.
Only explicit changed values compared against baseline; stale unchanged views don't
override current; independent field changes merge, incompatible same-field edits conflict.
Duplicate/missing identity surfaced by validator before reconcile. Pure
`reopenAncestors(records, changedIds)` -> updated cloned records and changed IDs; preserve
completed task facts, reopen relevant completed parents for unresolved tasks/DoD/blockers.
Do not write documents. Operation recovery plans rely on expected before/after values:
`recoverOperation(operation, actual)` -> report safe pending/already-applied/conflict,
never infer missing user intent.

Time module `lib/time/time.mjs`: `activityTime(reported, now?)` ->
`{activity_at,recorded_at,time_defaulted}`; reject malformed precise timestamps;
missing/ambiguous natural language falls back to now (caller preserves words).
`localDay(iso,timezone)` -> YYYY.MM.DD, `displayTime(iso,timezone)` always names zone.
Parse GMT via strict ISO UTC validation; no implicit local parsing.
