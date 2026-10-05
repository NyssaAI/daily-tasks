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
   carry. Explicitly deselected open work stays out. No timeframe fitting.
5. **Closure:** DoD, unresolved children and shared external blockers gate closure.
   Dependency is informational even when cancelled. Reopen propagates to closed parents,
   preserving completed tasks when blocker/DoD reopens.

Each is pass only if all listed assertions hold; any violation fails that scenario.
Unavailable authentication/host is Not run, not pass. A scenario executed through direct
code is evidence of code behavior only. Keep safe redacted attempts under attempts/ with
run ID, timestamps, source hashes, attempted command, last completed stage and next check.
No private account data or credentials in exports.

Deterministic coverage: test/log.test.mjs (persistence/concurrency/archive/corruption),
records/reconciliation/time tests (integrity and lifecycle), integration.test.mjs (templates,
CLI contract, isolated scope, packaged executable paths, carry-forward and user setup).
Verifier calibration: unit tests include valid/invalid metadata, precise timestamps,
corrupt JSON, conflicting operation reuse and valid closure; reject-all is not acceptable.
