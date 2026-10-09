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

Repository validation passes 144 tests, package assembly consistency and six-skill
contract validation. The final frozen source also passed all eight required Codex
native scenarios across 14 host turns. Source and 49 installed files stayed
unchanged. The required Node/Codex release acceptance gate passes; see the
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

The external review route was rejected by automatic approval review; no repository
payload was sent externally. The review used a local adversarial fallback.
