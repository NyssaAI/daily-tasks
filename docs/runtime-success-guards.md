# Runtime success guards

The audit found that instructions alone let an agent announce success without
checking actual effects. The CLI now owns supported objective completion checks;
skills still interpret requests, obtain acceptance and author Markdown.

| Boundary | Enforced check |
| --- | --- |
| Maintenance | Separate CLI inspection freshness from worker execution. Actual files, navigation, baselines and pending operations must pass before saving inspection state. No trusted host worker adapter is supplied, so worker success remains unrecorded. |
| Operation completion | Read actual before/after effects and protected sources; query and compare the complete exact event; validate proposed baselines and preserve unrelated entries before checkpoint removal. |
| Changed rollover | Check current/prior plan identities, nearest earlier plan, actual selected membership, task sources, removals and dated-state before hash. Support new plans, absent history and next-day recovery. |
| Migration retirement | Check copied criteria/content and remaining live path/UUID references before skill-owned deletion. Post-deletion completion requires retained source bytes, exact effects/event and checked baselines. It cannot prove earlier action order. |
| Navigation | Check local wiki, inline and reference-style Markdown destinations, headings and attachments. Inspection freshness includes target existence and heading fingerprints. |
| Record numbers | Inspect live labels and paginated queried retirement history. Preserve cancelled/retired numbers; distinguish unnumbered project history and legitimate legacy first-label migration. Ambiguous history blocks allocation. |
| Log access | Supported scanners exclude hidden log directories. Log access goes through the log API. Unrestricted host file tools remain outside CLI enforcement. |

New checkpoint inputs and operations are documented in the canonical
[verification contract](../skills/daily-tasks/references/verification.md) and
[CLI interface](../skills/daily-tasks/references/cli.md). No command writes or
deletes user Markdown as part of these guards.

Nine local review lenses and an independent finding validator confirmed eight
defects in the first implementation. All eight were repaired with filesystem
regressions: Markdown destination normalization, pending rollover state,
holding-area scope, reference links, project lifecycle numbering, next-day
recovery, optional daily-plan storage and attachment freshness. Additional tests
exercise nonempty carry/removals, first-plan creation, stale state hashes,
task-shaped prior plans and retired UUID references.

Repository validation passes 145 tests, package assembly consistency and six-skill
contract validation. The earlier frozen source also passed all eight required Codex
native scenarios across 14 host turns. Source and 49 installed files stayed
unchanged. That candidate passed the required Node/Codex release acceptance gate; see the
[latest evaluation](../evals/LATEST.md) and
[final native receipt](../evals/results/codex-native-dabf0f6f-20261009/result.json).
The requested model was `gpt-6.1-sol`; backend model metadata was not independently
exposed. Other optional hosts remain unverified.

Native probes also exercised cancellation snapshots wrapped under `records`,
append-only corrections and descriptive output-renaming events. The allocator
retains all known labels across corrections and exempts path-only artifact events
only when their paths prove holding-area scope. Focused failures remain retained
alongside the final passing full suite.

A focused follow-up review also required prior snapshots for every affected record
in ordinary cancellation and migration events. Only an explicit
`task.cancel-and-accept` event may introduce an after-only new record. Regression
checks retain the prior label when a correction supplies missing history.
Native evidence also caught a solver putting a newly created record into before
as inferred label facts. That run is retained as a failure. Explicitly marked
non-observed prior snapshots now block allocation, and canonical guidance names
the mixed-event action and prohibits invented history. The CLI cannot authenticate
arbitrary unmarked agent-written observations; a trusted host capture adapter
would be required for that stronger guarantee.

The first fresh full suite passed six scenarios and failed day-change and migration.
Migration failed because a concrete, unnumbered legacy DoD retirement blocked
later numbering. The allocator
now recognizes that supported legacy type only with concrete identity, path and
milestone parent; numeric-looking or parentless DoD history remains ambiguous.
The failed full run remains retained alongside the corrected full-suite pass.
Day-change failed because an agent-authored recursive evidence hash walk read raw
decision-log bytes in nested scratch vaults. Query-only guidance now explicitly
covers checksums, evidence capture and hidden log directories at every depth.
Supported CLI scanners already exclude those directories; arbitrary host file
tools remain outside this enforcement boundary.

The first 0.3.4 native run passed six scenarios and failed closure and migration.
Closure omitted an explicitly proposed milestone reopening before a later repair.
Migration appended its success event after retirement inspection refused live
references, leaving the original document and checkpoint present. Those failures
remain retained. New `workspace.migration` log entries now require the bound
checkpoint and verified retirement, preserved criteria, declared file effects
and protected hashes before persistence. Exact already-recorded retries remain
idempotent after checkpoint clearance. A filesystem regression failed before
this guard and passes with it; independent local review found no defects.

The next 0.3.4 native run passed seven scenarios and failed day-change. Its initial
rollover checkpoint declared empty carry without deriving against the new plan
identity; completion refused it. A second operation left the original pending,
and its renderer nested a full carried row presentation inside another link.
The failed run remains retained. General rollover guidance now explicitly derives
final carry against the new stable plan UUID and renders one link from the
canonical task title or parsed label, with carry and assignee context outside.

The resulting 0.3.4 candidate passed all eight native scenarios across 14 host
turns, with source and 49 installed files unchanged. The current required
Node/Codex release gate passes; see the
[0.3.4 native receipt](../evals/results/codex-native-c8f8bf4f-20261009/result.json).
Its evidence retains an initial checker access error: independent byte comparison
proved the historical plan unchanged, with completed and cancelled rows intact.
Closure also retains a misleading custom operation label whose declared actual
snapshot left the blocker open; task completion remained refused until a verified
repair resolved it. The log checks declared effects, not free-form action semantics.
Completion checks can verify declared effects, but cannot reconstruct requested
intent that an agent omits from its checkpoint.

The external review route was rejected by automatic approval review; no repository
payload was sent externally. The review used a local adversarial fallback.
