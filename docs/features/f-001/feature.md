---
id: F-001
phase: 0
status: implemented
document-maturity: reviewed
---

# F-001 Project inventory with configurable freshness

## Summary

Provide a separate deterministic operation that indexes projects and their open
tasks into a timestamped JSON summary. Daily planning uses the summary to discover
available work alongside previous daily selections, with configurable cache reuse.

## User Need

The user needs daily planning to consider work across the projects directory, not
only tasks carried from an earlier plan. A compact inventory reduces repeated agent
file exploration while retaining canonical Markdown authority and visible freshness.

## Use Cases

None yet.

## Scope

- Index canonical projects, milestones, open tasks and relevant blockers beneath
  the resolved projectsRoot through an independent executable operation.
- Summarize task identity, title, relative path, lifecycle state, human owner,
  optional assignee, explicit target date, project/milestone relationships,
  dependencies and blocker references. Include project/milestone titles and states
  and relevant blocker titles, states and impacts.
- Collect explicit persisted future-day selections from daily-plan records, matching
  task UUIDs rather than titles. Add one `planned` array to each open task summary;
  each entry contains `date` and `source`. Dates use YYYY.MM.DD without a time or offset.
  Preserve these calendar dates across hosts and timezone changes. Resolve today
  using the effective timezone, then compare dates for selection eligibility;
  never convert a planned date through UTC or shift it to another calendar day.
  Keep future-allocated tasks in the inventory and full open-task counts. The
  selection screen excludes tasks with a planned entry dated later than today.
  A target_date is a due date, not an allocation. Never infer planning from it.
- Use dated daily-plan files as the sole durable authority for planning dates.
  An explicit future selection creates the destination day's daily-plan file if
  absent, using the configured daily-plan template. There is no separate allocation
  store. This indexer reads those files; the planning skill owns their writes.
- Each task has at most one active planning date. Its `planned` array contains zero
  or one entry for today or a future date. Earlier daily-plan rows remain historical
  and do not count as additional active dates. Moving a selection transfers it from
  its current active day to the destination day without changing historical plans.
  Conflicting active dates produce a diagnostic and require clarification; do not
  silently choose one. Pending review decisions suppress repeat suggestions within
  that review without masquerading as committed selections in the inventory.
- Diagnose missing/duplicate task identities and ambiguous allocation sources rather
  than assuming a future task is available. A known allocation change invalidates
  the affected summary even before inventory TTL expiry; its next use must reflect
  that change. Cache reuse must not reintroduce work moved to a future day.
- Write derived cache at `<vaultRoot>/.temp/daily-tasks/project-index.json`.
- Include schema version, UTC `generatedAt`, source fingerprints and diagnostics.
- Use the agreed [inventory JSON shape](inventory.example.json). Sort projects by
  the date in their directory names, oldest first, with name as the tie-breaker.
  Dated directories precede undated directories; undated directories sort
  alphabetically by name. Preserve milestone order within each project and task
  order within each milestone from project indexes. Store that order in arrays,
  without duplicate position fields. Directory dates are calendar dates, not instants.
- Store planned dates and their source together only once, under `planned`; omit
  dates-only arrays, counts, lateness flags, future-date flags, eligibility flags and
  lowest-incomplete-milestone summaries. Compute these on read using current identity,
  the effective timezone/local day and the recorded lifecycle states and order.
- Configure nonnegative integer `projectIndex.ttlSeconds` in the effective profile;
  initialize its default to `14400` (four hours). Zero disables cache reuse.
- Always rebuild on explicit refresh. When needed otherwise, rebuild if absent,
  malformed, incompatible, known stale or scoped incorrectly, or age >= TTL.
- Before cache reuse, perform lightweight source-change checks, including project
  directory membership and relevant project/daily-plan file metadata. Detected
  additions, deletions, moves or edits invalidate the cache before TTL expiry.
  Plugin writes immediately invalidate affected cached data. Refresh source hashes
  during rebuild; do not equate unchanged metadata with proof of unchanged content.
- Treat missing/future timestamps as unusable. Read/copy operations never reset age.
- Detect added, deleted and moved records during refresh, preserving UUID identity
  and reporting missing/duplicate identities or invalid metadata.
- Write atomically. A failed refresh reports failure and does not advance the
  successful refresh timestamp or represent old data as current.
- Supply available work to planning separately from already selected work.
- Use direct CLI execution for routine inventory reuse or refresh. When the broader
  reconciliation pass requires a subagent, let that same worker obtain/refresh this
  inventory; do not spawn a separate worker solely for deterministic indexing.
- The shared maintenance worker uses an available lightweight model: `gpt-6-luna`
  in the current Codex harness, Haiku in Claude, or a comparable lightweight model
  supported by another host. Pass explicit model selection when supported. If a host
  cannot select a worker model, report that limitation; deterministic indexing can
  still run directly. Do not claim lightweight execution from a Markdown declaration.
- Surface changed editable views for reconciliation before affected statuses inform
  planning. Within TTL the inventory remains a dated snapshot; consequential
  changes still require current canonical checks and reconciliation.

## Out of Scope

- Selecting or accepting tasks, choosing daily priorities, or authoring daily plans.
- Completing tasks, resolving conflicts or writing canonical Markdown.
- Owning durable selections, pending operations, decision history or reconciliation
  baselines; deleting the inventory loses none of these.
- Background refresh, monitoring, automatic scheduling or fitting work into time.
- Full task execution instructions and reference contents in the summary.
- The portable-path resolver, personal/vault preference layering, frontmatter ID
  migration and baseline reconciliation. Related resolver, frontmatter-ID parsing
  and table parsing are delivered alongside this feature; no automatic migration occurs.
- Authoring future daily plans or owning the durable allocation workflow. The
  planning skill creates/updates dated daily-plan files and enforces one active
  planning date. The related planning skill owns checkpointed Markdown persistence;
  the indexer only reads committed rows and diagnoses conflicts.
- Implementing the shared reconciliation worker or its four-hour full-reconciliation
  gate. This feature defines the inventory interface and lightweight delegation
  policy; reconciliation has a separate success timestamp and owns its own behavior.

## Inputs

- Explicit resolved vaultRoot and projectsRoot supplied by the calling skill or
  context resolver; indexing must not derive scope from its subprocess cwd.
  A session has one vault and its assigned projects root. A root outside vault/home
  storage uses the logical `@projectsRoot` alias in cache scope; the resolved path
  stays in the session context. Shared user preferences never combine vaults.
- Canonical Markdown records and relevant editable project views under projectsRoot.
- The resolved dailyPlansRoot, configured timezone/local day, and authoritative
  persisted selections in dated daily-plan files, keyed by task UUID.
- Effective `projectIndex.ttlSeconds`, defaulting to `14400`.
- Existing inventory, when present, and its source fingerprints/schema/timestamp.
- An explicit refresh request, or a request to obtain inventory for planning.
- Current UTC time for refresh timestamps and TTL age comparisons.

## Outputs

- `<vaultRoot>/.temp/daily-tasks/project-index.json`, a disposable derived summary
  containing paths relative to projectsRoot, without host-specific absolute paths.
  Task summaries include `planned` entries with `date` and `source`; source plan paths are
  relative to vaultRoot, distinctly anchored from project record paths.
  The top-level shape is `schemaVersion`, `generatedAt`, `scope`, `projects`,
  `milestones`, `tasks`, `blockers`, `sources` and `diagnostics`, as illustrated in
  [inventory.example.json](inventory.example.json). Scope contains `projectsRoot`
  and `dailyPlansRoot`; the current effective timezone is resolved when consuming
  the inventory rather than persisted as a display or date-comparison convenience.
- An operation result distinguishing successful rebuild, valid cache reuse and
  failure, with timestamp/freshness and integrity diagnostics.
  The result also carries the resolved planning binding for the caller to pass
  into planning operations; it is not an inventory convenience field.
- Changed-view indications for the reconciliation workflow; these are observations,
  not accepted state transitions.

## Acceptance

- Open tasks across multiple projects appear even if never selected in a daily plan.
  Completed/cancelled tasks do not appear as open work.
- Owner/assignee, milestone/project relationships, explicit target dates,
  dependencies and blockers reflect canonical sources without inferred acceptance.
- A task selected for tomorrow or another future date retains its open-task summary
  and contributes to open counts, but is excluded from today's addition options on
  every page. Each planned date and source identity appears together in `planned`,
  without a separate duplicate dates array.
- A task has zero or one active `planned` entry. Multiple historical plan rows do
  not violate this rule; selections on multiple current/future dates produce a
  diagnostic and are not silently collapsed into an apparently valid selection.
- Projects with directory dates appear oldest first, with alphabetical name
  tie-breaking; undated projects follow alphabetically. Milestone/task order comes
  from project indexes, not filesystem enumeration, task due dates or UUIDs.
- Counts, lateness, future-date eligibility and the lowest incomplete milestone are
  derived on read, including after midnight or a timezone change without requiring
  a rebuild merely to update those computed values. Source array order is preserved
  and supplies ordering without additional position fields.
- A task with a future due date but no future selection remains eligible. Moving,
  removing or changing a future selection updates eligibility on next inventory use
  when the change is known, even inside the four-hour TTL. Matching survives task
  renames and moves because allocation joins use UUID, not display titles or paths.
- An ambiguous or unidentified future selection produces a diagnostic and is not
  silently treated as evidence that the corresponding work is unallocated.
- Invalid structured record text is diagnosed without guessing a state. An invalid
  task is withheld from additions; an invalid project/milestone retains a scoped
  barrier so later milestones cannot become eligible accidentally. Preserve existing
  selections and unrelated projects. Filename advice alone does not hide work.
- Inventory generation does not select work or mutate canonical Markdown, logs,
  reconciliation baselines or pending operations.
- Paths are relative to projectsRoot and the cache is at the specified vault `.temp`
  location. Removing the cache permits a complete rebuild without losing durable state.
- With TTL 14400, a compatible cache just below four hours is reusable; at four hours
  or later it rebuilds when requested for use. Explicit refresh rebuilds before expiry.
- Reuse below TTL checks for source changes first. Detectable external edits and
  directory membership changes invalidate cached data; plugin writes invalidate
  immediately. A source-check failure cannot be reported as confirmed freshness.
- TTL zero rebuilds whenever needed. No operation runs solely because time passes.
- Missing, malformed, incompatible, known-stale or incorrectly scoped cache and
  missing/future timestamps trigger rebuild when needed; invalid TTL is diagnosed.
- Added/deleted/moved records and duplicate/missing IDs produce current inventory
  and diagnostics after refresh. Changed views reach reconciliation before affected
  task statuses are used to plan.
- Failed refresh preserves the previous successful cache and reports failure without
  a new generatedAt or a false freshness claim. Successful writes are atomic.
- Summaries omit full task instructions; detailed files remain available for selective
  loading by the planning skill.
- Behavior and integration checks use `node --test`, synthetic records, and measured
  cold/reused operation durations and file-read counts. No numerical latency target
  or verified performance improvement is claimed before measurement.
- Generated packages preserve the operation and skill integration, checked with
  `node scripts/assemble.mjs write` followed by repository packaging validation.
- Routine indexing does not require a subagent. When called by a shared maintenance
  worker, the host's actual lightweight model selection is verified or its exact
  limitation is reported; indexing success does not advance reconciliation freshness.

## Dependencies

- Existing canonical Markdown identity, parsing, lifecycle and relationship contracts
  in [record conventions](../../../skills/daily-tasks/references/records.md).
- Existing reconciliation protocol for changes observed in editable views;
  [operation protocol](../../../skills/daily-tasks/references/operations.md) owns
  reconciliation and persistence of accepted changes.
- Resolved vault/project scope and permitted filesystem/process access on Node >=22.
- The shared table parser observes project-index edits. Differences require baseline
  reconciliation before affected tasks appear as available additions.
- Durable future-day selections in dated daily-plan files, including selected-row
  parsing, task UUID references, moves/removal and enforcement of one active date,
  are read by the inventory and covered by the planning-skill protocol. Planning writes use the existing recovery
  protocol so a partial transfer cannot be reported as a successful move.
- Agreed product contract in [requirements R16](../../requirements.md).

Implemented in `lib/inventory/inventory.mjs`, with CLI, synthetic integration and
failure-path tests in `test/inventory.test.mjs` and `test/integration.test.mjs`.
Local package verification does not establish native-host skill activation or
successful execution of agent-authored Markdown transactions.
