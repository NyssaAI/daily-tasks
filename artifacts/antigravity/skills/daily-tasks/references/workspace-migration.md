# Migrate an existing milestone workspace

Migration is a skill-owned Markdown operation, using the existing operation protocol.
The CLI inspects, validates and proposes; it does not move or rewrite user documents.
An installation/update alone does not authorize conversion. Use the user's requested
scope, resolved roots and existing identities; never discover personal data elsewhere.

1. Inspect the milestone, standalone DoD, tasks, backlinks and current per-view
   baselines. Reconcile outstanding edits before migration. Inventory all affected
   files, including attachments and old navigation paths. Reuse recorded milestone
   and task numbers when unambiguous; otherwise allocate unused parent-local numbers
   as described in records. Compare destination paths case-insensitively on Windows.
   Existing unrelated destinations or duplicate identities are conflicts, not overwrite
   permission. Legacy records stay usable while conflicts are resolved.
2. Prepare the concrete file/path and identity mapping. Preserve milestone/task UUIDs,
   lifecycle, owner, assignee, timestamps and relationships. Copy existing milestone
   criterion text, checked state, evidence and criterion UUIDs into its own DoD section.
   If both embedded and standalone criteria already exist, reconcile their authority
   explicitly; never combine them blindly or let closure choose one source.
3. Review each task's requirements and task-specific DoD. Retain an already accepted
   criterion; request missing acceptance facts without manufacturing checked criteria
   from completed status. Do not copy milestone criteria into every task. Legacy tasks
   without accepted criteria remain unversioned until this is resolved; report them
   as pending migration. Completed history stays intact. When newly accepted criteria
   are unsatisfied, propose the required reopening explicitly through the protocol.
4. Checkpoint exact before/after file bytes or recoverable references, content hashes,
   path mappings, retired standalone DoD identity, criterion IDs, relationship changes,
   timestamps, event/operation IDs and intended log payload before writing. Recovery
   copies stay in the project's .temp/ so scanners do not see duplicate live records.
   Include file absence/presence in effects. Recovery must distinguish a completed
   move from a missing file; do not treat disappearance as authorization.
5. Write the milestone and prepared task files with record_version: 2. Create flat
   inputs/ and outputs/; move task files beside the milestone, not into task folders.
   File task-owned inputs/deliverables in those holding areas and link them from tasks.
   Preserve shared originals by reference, without making duplicate working copies.
   Verify destination bytes before removing old working files. Intermediate duplicate
   IDs require pending recovery; do not run planning or publish completion mid-move.
6. Retarget live references to the retired DoD document to the milestone's
   `#Definition of Done` heading using the milestone UUID. Keep criterion references
   on their original criterion UUIDs. Transfer any standalone DoD blocker relationship
   to the milestone and update reciprocal blocker links. Preserve notes and provenance;
   do not discard non-criteria content. Retain the old DoD UUID in migration history,
   not as a second active record. Do not rewrite historical decision-log entries.
7. Update incoming and outgoing relative links across maintained records and views,
   including task input/output links and links within moved notes. Project index links
   milestone; milestone links tasks; tasks link relevant files. Verify heading targets
   and attachment links in addition to CLI identity/link diagnostics. Remove the old
   live standalone DoD only after destination and references verify. Validate final
   records, closure/reopening effects and navigation; append and query the exact
   migration event via log CLI, refresh views/baselines, invalidate inventory, then
   finish the checkpoint. Keep unchanged history and unrelated prose intact.
8. On retry, compare each checkpoint effect to its actual before/after value and skip
   applied effects. Reuse the event IDs and payload, checking through log-query so
   there is one event. Unexpected edits remain conflicts. Report migrated records,
   legacy tasks awaiting criteria, and remaining conflicts with exact links.
