# Daily Tasks evaluation

`node evals/run.mjs` runs the declared deterministic suite and package checks, retaining
raw stdout/stderr, exit codes, source inventory, platform and Node version. It never
claims native skill discovery or behavioral host acceptance. Each test assertion is a
binary criterion; report actual test counts, not a fabricated general agent score.

`node evals/report.mjs write` generates LATEST.md; `check` validates evidence hashes,
candidate freshness and exact report contents without changing it. `release` additionally
requires every matrix target verified; this intentionally fails while hosts are unverified.
Results preserve failures, not only passes. Source files and generated runtime artifacts
are frozen before evaluation; results/attempts/LATEST and dated review receipts are excluded.

## Native skill scenarios

### Planning recovery fixture

`node evals/planning-fixture.mjs seed ABSOLUTE_SCRATCH_DIR STAGE` creates an isolated
synthetic vault and returns its manifest path. STAGE 0 is before writes; 1 is after
destination persistence; 2 after source removal; 3 after decision append; 4 after
baseline update. All start with a pending checkpoint. Generated UUIDs, exact hashes,
accepted move intent, unrelated rows/prose, historical plan and dated rollover state
are retained in the manifest. This initializer does not resume operations.

In a native skill run, give the agent that vault and ask it to resume its existing
pending move using the installed operation protocol. Observe each file-tool write,
CLI log append/query, inventory invalidation and completion. Run
`node evals/planning-fixture.mjs inspect ABSOLUTE_FIXTURE_JSON` afterward: all effects
must be already applied, one active date and one exact event must remain, unrelated
prose/rows and history must survive, and rollover removal state must preserve prior
receipts. Retry again without another event. Inject an unexpected file/baseline edit
or mismatched event payload and require conflict without a completion receipt.

`node --test test/recovery-flow.test.mjs` exercises every stage through a test-only
writer and public integrity/log/cache APIs. It is cross-feature regression evidence,
not native discovery. Current-chat file-tool runs and real model-worker runs also
remain separate from fresh isolated host acceptance.

### Maintenance and phone checks

Use a clean fixture with no pending operation. Retain the actual subagent invocation,
model and worker output, installed skill paths and observed hashes. Missing/expired
maintenance success should trigger the supported lightweight worker. The parent
verifies results before persisting success; a failed/conflicting pass leaves the old
success unchanged. A second request within four hours skips broad delegation but
still checks current/previous plan edits and pending operations. Cache freshness alone
cannot prove reconciliation success.

For phone continuity, persist one vault's numbered screen and mapping binding in its
stateRoot in the Windows app. Continue that same chat on the phone with an explicit
status reply. Verify canonical/project writes precede daily-plan updates, stable task
IDs, the host timezone, unchanged binding and no duplicate event. Try a mapping from
another fixture vault and require rejection. Record the user's device confirmation;
desktop automation cannot establish that the reply arrived through the phone.

### Six acceptance scenarios

Run these with a fresh authenticated host, explicit plugin registration and synthetic
vault outside personal state. Record actual loaded skill paths, host version/model when
exposed, fixture before/after, actions, decision-log queries and whether each condition
passed. Do not use a loaded project AGENTS.md as proof of plugin discovery.

1. **Acceptance:** supply an ambiguous request and manual new checkbox. No accepted task
   is created until explicit batch acceptance. Then all records have metadata and UUIDv7.
2. **Assignment and time:** default owner from setup, omitted assignee means owner;
   agent can assign but cannot autonomously change owner. Retrospective vague start uses
   now plus original words. GMT storage, local display with explicit timezone.
3. **Reconciliation:** stale unchanged plan vs updated definition does not reopen it;
   changed checkbox does. Conflicting completed/cancelled edits remain pending, unrelated
   work proceeds. Retry interrupted log append yields one decision.
4. **Day change:** check in after skipped days. Only today is created; unfinished selected
   own/delegated work carries. Completed/cancelled remains visible yesterday but doesn't
   carry. Explicitly deselected open work stays out. No timeframe fitting. Repeat with
   Tuesday pre-created with B while Monday contains unfinished A: Tuesday retains B
   and carries A once. Remove A, repeat Tuesday, and verify A stays removed. Interrupt
   rollover after destination persistence and recover without duplicate rows/logs or
   a false completion receipt. Explicit future-day removals remain honored.
5. **Closure:** DoD, unresolved children and shared external blockers gate closure.
   Dependency is informational even when cancelled. Reopen propagates to closed parents,
   preserving completed tasks when blocker/DoD reopens.
6. **Configuration discovery and direct acceptance:** supply a known vault, existing
   Job Search project, user email/timezone and accepted common `.nyssaai` state root.
   Ask "Create M1: update LinkedIn and resume in this project." With no configRoot
   argument, the agent must load `<common-state-root>/daily-tasks/profile.json`, reuse
   the project, and create that accepted milestone without a directory/setup/acceptance
   question. Repeat with no profile: initialize conventional state from known context,
   use empty priorities if none were supplied, and continue. No invented extra tasks.
   Check milestone output is in the project, daily-plan output is in the configured
   vault output directory, and only configuration/operating state is in `.nyssaai`.
   Repeat with an explicit legacy profile pointer (reuse, no migration), a known vault
   with only its legacy profile (reuse), unknown vault scope (ask for scope, not an
   internal directory), and conflicting applicable profile values (preserve and ask).
   Reuse one home profile in two vaults: projects, plans and operating state must
   remain independent. A numbered reply, inventory or checkpoint from the first
   vault cannot operate in the second; the agent must keep a separate session.

Automated parser/allocation checks cover adjacent next-line references, conflicting
references and legacy cancellation, including unchanged stale views after reopening.
These checks do not substitute for the six native skill-authored scenarios above.

Each is pass only if all listed assertions hold; any violation fails that scenario.
Receipt IDs are `acceptance`, `assignment-time`, `reconciliation`, `day-change`,
`closure`, and `configuration-discovery`. All six are required; five cannot pass.
Unavailable authentication/host is Not run, not pass. A scenario executed through direct
code is evidence of code behavior only. Keep safe redacted attempts under attempts/ with
run ID, timestamps, source hashes, attempted command, last completed stage and next check.
No private account data or credentials in exports.

Deterministic coverage: test/log.test.mjs (persistence/concurrency/archive/corruption),
records/reconciliation/time tests (integrity and lifecycle), integration.test.mjs (templates,
CLI contract, isolated scope, packaged executable paths, carry-forward and user setup).
Verifier calibration: unit tests include valid/invalid metadata, precise timestamps,
corrupt JSON, conflicting operation reuse and valid closure; reject-all is not acceptable.
