# Tessl guidance implementation and evaluation

Composition changes U1–U3 are implemented on `improve/tessl-guidance`, through
commit `942a990`, against baseline `d20b74b2ff5d85e064bea890c89e9fe9cf6b057e`.
U4 evaluation is complete for the two planned optimization iterations. Required
native acceptance fails; this report does not establish release acceptance.

## Composition

The six existing skills remain the composition. Their shared references, templates
and Node CLI support the workflows; no always-on product rule, slash command,
lifecycle hook, MCP server or additional skill was added. Maintenance remains
request-triggered. Runtime algorithms, record schemas and version 0.3.3 are unchanged.

Four descriptions now carry explicit triggers. Requirements distinguish a user's
direct named creation instruction from quoted requests, inferred promises and new
manual checkboxes. Plan follows six ordered checkpoints, with shared policy moved
from template comments to its owning references. The CLI summary includes both
required inventory/review hashes and a complete packet-derived input example.
Planning instructions consistently name the six existing columns.

## Local verification

- All 105 existing tests pass; no wording-only tests were added.
- All 174 generated files match canonical source; all six skills validate.
- Markdown audit: no broken links or orphaned support files; JSON examples parse.
- The exact new JavaScript example passes syntax validation and was exercised
  through the CLI in a synthetic vault: review saving, no-change rollover and stale
  source/state rejection succeeded.
- A focused correctness review and a separate Sol 6.1 adversarial read found no
  actionable composition defects. An attempted external review produced no usable
  artifact and was replaced by the separately dispatched local reviewer.
- The recorded deterministic run
  [2026-10-09T15-25-43-738Z-41392](../evals/results/2026-10-09T15-25-43-738Z-41392/result.json)
  passed against frozen candidate
  `c6931c62c8c3530b7d6b117ef19f14b50fc8efce36c48bc2160df3c07c33227e`.
  `evals/report.mjs check` verified its evidence and generated report.

The new evaluation suite has 14 activation cases and five task scenarios. Fixture
QC exercised all nine initialization modes twice, checked repeatable identities,
and verified that the rollover proposal adds earlier task A while preserving
pre-created selection B. Nineteen duplicate initializers were consolidated into one
fixture file, reusing the existing recovery initializer. Separate reuse, quality
and efficiency reviews found no further worthwhile simplification. One unused
import was left unchanged as a low-value cosmetic edit after fixture freeze.

A separate adversarial fixture review found that the recovery checker source was
still visible to the evaluated agent. Fixture version 4 removes both setup source
files before agent execution. All 19 setup scripts were executed in isolated
workspaces: both sources were absent and the production CLI remained usable.
The fix is committed as `4d67520`; earlier activation evidence retains its fixture
version and cannot silently stand in for the corrected fixture.

## Instruction quality

Tessl reviewer: `tessl/default-skill-review@0.2.0`. Scores measure instruction
quality, not task execution or activation. The returned JSON does not identify
the serving judge model; no exact model-equality claim is made.

| Skill | Before | After | Change |
| --- | ---: | ---: | ---: |
| Router | 82 | 90 | +8 |
| Setup | 79 | 76 | -3 |
| Capture | 75 | 87 | +12 |
| Records | 79 | 84 | +5 |
| Plan | 68 | 91 | +23 |
| Check-in | 75 | 89 | +14 |

Changed rubric dimensions (1–5 scale; omitted dimensions were unchanged):

| Skill | Description dimensions | Content dimensions |
| --- | --- | --- |
| Router | Specificity 4→5; distinctiveness/conflict risk 4→5 | Conciseness 4→5; progressive disclosure 4→5 |
| Setup | Completeness 5→4 | None |
| Capture | Specificity 4→5; completeness 3→5; trigger terms 3→4 | None |
| Records | Completeness 3→5; distinctiveness/conflict risk 3→4 | Conciseness 5→4 |
| Plan | Specificity 4→5; completeness 3→5; trigger terms 3→4 | Conciseness 4→5; workflow clarity 3→5; progressive disclosure 3→5 |
| Check-in | Completeness 3→5 | Actionability 3→4; workflow clarity 4→5; progressive disclosure 4→5 |

Setup's entire score reduction came from its unchanged description. Router's
unchanged description also received higher scores. These single-run differences
show judge variability; they do not establish an execution regression or a causal
gain. The clearest aligned result is Plan's improved workflow-clarity assessment.

All six reviews passed structural validation with zero errors and one relative-link
warning each. Individual child uploads omit sibling references; complete-package
inspection verifies those references actually ship. Duplication would obscure their
single owner and is not an appropriate warning fix.

Setup and Records remain below the advisory 85 target. Setup feedback favors clearer
sectioning, stronger settings-update triggers and a linear validation/save procedure.
Records feedback favors moving more detail to shared references. These suggestions
remain advisory while behavioral evaluations run; no safeguard, schema or capability
was changed merely to increase a score. Capture suggestions for a new candidate
schema exceed this refactor's preserved-schema scope. Router examples and duplicated
conflict handling belong to its routed workflows. Existing operation/recovery rules
remain authoritative even when an isolated reviewer cannot load them.

Full before/after and security receipts are retained in
[the review evidence directory](../evals/attempts/2026-10-09-tessl-guidance-review/).

## Packaging and security

Disposable original/revised Tessl wrappers were separately staged. Parent `.temp`
ignore rules initially caused incomplete archives; a private scratch Git boundary
resolved that. Tessl's content-selected packaging excludes root runtime directories,
so both evaluation wrappers carry identical runtime assets under the existing
router skill. This is evaluation infrastructure, not a new installation format.

Both final archives contain all 37 intended source members: 19 skill/support files
and 18 runtime files. Every intended member was checked against its source bytes.
Both unpacked CLIs work from an unrelated working directory. This proves local
packaging/execution, not cloud sandbox or native skill acceptance.

Six security reviews returned `verdict: pass`, `securityLevel: NONE`,
`overallSeverity: LOW`, and no findings. The router review included its staged
runtime assets; the other five reviews covered their own skill directories.
The CLI rejected a full-wrapper review because it requires a root SKILL.md, so no
single-review coverage of the whole plugin is claimed.

## Activation, task performance and native host

Explicit Tessl Codex/Sol 6.1 selection was rejected by the connected account's
paid-model entitlement. No upgrade was performed. Supported solution recipe
metadata identifies the actual cloud solver as `claude/deepseek-v4.1-flash` and
judge as `claude/claude-sonnet-4-6` in both comparisons. These are free-default
cloud results; requested Sol 6.1 implementation/review and native tests are separate.
The instruction-quality reviewer above still does not expose its serving model.

The [14-case natural run](https://tessl.io/eval-runs/01a1211c-f878-7382-ada2-f3d0d7bb243a)
and [two corrected mapping cases](https://tessl.io/eval-runs/01a12121-9c01-74ca-83b4-65e06d88cfc4)
completed with forced activation and scoring disabled. A10/A14 use the corrected
run because the original mapping was inverted. Final workspace downloads establish
saved effects: A03/A06/A12 remain candidates; A04 reassigns without starting;
A07/A08 create exactly the requested one/two tasks; A05 carries prior selection;
A11 completes Review and selects Draft without starting; A14 completes Review
while retaining the unaccepted announcement; A10 leaves plan/state/log unchanged.
A09/A13 leave accepted records unchanged despite unnecessary skill reads.

These observations are partial activation evidence. Reads alone do not establish
workflow choice. Downloads contain final files, not full dialogue or ordered tool
calls, so questions, screen rendering, checkpoint ordering and fixture-source reads
remain unverified. Earlier natural fixtures exposed initializer/oracle sources.
Browser retrieval hung and was aborted; `eval debug` required Tessl-organization
membership. No aggregate activation percentage or full workflow pass is assigned.

Seven explicit direct-child runs and four affected iteration1 reruns completed.
Downloaded bundles match all 37 required sibling/runtime members; initializer and
oracle sources are absent. These runs name the entry file in `agentMustRead` while
global forcing/scoring are disabled, so they test explicit dependency execution,
not natural routing. Records, Capture, Setup and Plan saved effects respect their
observed boundaries. Iteration1 Check-in leaves the announcement pending and Draft
not-started, but completes Review from existing checked DoD/Result. Final files
cannot establish confirmation scope or ordering; that case remains qualified.

The first v4 content run
[01a12130](https://tessl.io/eval-runs/01a12130-1e05-73bb-a0b3-1e8fa6f68e77)
is invalidated: stale `resources/seed.mjs` survived overlay staging and was
auto-included. The replacement
[clean five-case comparison](https://tessl.io/eval-runs/01a12135-d04c-7286-9ee5-ff722bfd91bb)
completed 15/15 cells after fresh staging verified all 20 fixture files and absent
seed. The [iteration1 comparison](https://tessl.io/eval-runs/01a12148-97ac-7268-af40-cd67022aab14)
completed 9/9 cells for the three affected scenarios against frozen candidate
`c6931c62c8c3530b7d6b117ef19f14b50fc8efce36c48bc2160df3c07c33227e`.
Both use no-context, original and revised conditions with common runtime support;
forcing/scoring are enabled. Exact criterion totals, rather than truncated display
scores, are:

| Comparison | No context | Original | Revised |
| --- | ---: | ---: | ---: |
| Initial clean five scenarios | 14/20 (70%) | 19/20 (95%) | 19/20 (95%) |
| Iteration1 three affected scenarios | 7/12 (58.33%) | 12/12 (100%) | 11.7/12 (97.5%) |

Iteration1 baseline solution IDs and fingerprints are cached unchanged controls
from the initial run. Do not combine the two unchanged initial cases into an exact
final five-case average. Initial revised closure and rollover each total 3.5/4
(87.5%), although Tessl displays 87. Closure saved an explicitly requested
not-started task as in-progress: a confirmed failure. Rollover deductions concern
missing dialogue evidence, not established saved-effect failures. Initial original
recovery scores 3/4 because the judge claims the original checkpoint was absent;
setup QC creates it, but final files cannot establish its initial use. That raw
score remains unchanged.

Iteration1 revised rollover and recovery score 4/4 each; closure scores 3.7/4
(92.5%, displayed 92). The explicit not-started state is now correct. Its remaining
deduction combines retained checked DoD and retained `started_at`. Preserving the
known start follows canonical history policy and is not a new execution start;
the rubric does not require clearing it. The checked criterion records prior
approval, while reopening for revision raises a question about its current
satisfaction. Current policy expressly covers user-unchecked DoD but does not
clearly settle whether this wording revokes prior approval. Treat this as a
remaining guidance/semantic uncertainty, not an established start-retention defect
or a silently adjusted pass. The raw 0.7 criterion remains in the receipts.

The existing recovery oracle passes all three final iteration1 arms: canonical
records, history, identity, prose, rollover, one log, one active destination and
checkpoint clearance are preserved. Downloaded JSON bytes remain untouched;
inspection locators are rebased and expected hashes use the actual cloud sandbox
root and identical seeded IDs. Final effects still do not prove dialogue/order.

Safe cloud summaries, original criterion reasoning, recipe metadata, fixture QC,
bundle verification and oracle receipts are retained in
[the evidence directory](../evals/attempts/2026-10-09-tessl-guidance-review/cloud/).

Fresh isolated Windows Codex 0.161.0 discovery with requested `gpt-6.1-sol` succeeded
and read the installed router. Two complete eight-scenario native runs are retained
below, with failures preserved and exact source windows. Earlier exploratory runs
remain supplemental rather than being backdated to a later inventory.
Phone continuity and optional hosts remain separately unverified.

## First optimization iteration

The first complete native run is retained as a
[hash-verified failure](../evals/results/codex-native-996365-20261009/result.json):
six scenarios passed; day-change and workspace-migration failed. Rollover changed
two existing plan creation timestamps before subsequent corrected operations.
Migration removed the old standalone DoD while three still-live legacy task sources
still linked to it. Clean final destinations did not establish safe intermediate
deletion order. Both failures were independently confirmed from saved bytes and
operation effects; later repairs do not erase them.

Cloud output also saved Draft landing copy as `in-progress` despite an explicit
request for `not-started`. The code's unchecked-box fallback was applied before
the user's intended task state was supplied. The correction puts that explicit
state into the proposed records before calculating required parent effects.

Commits `60ca768` and `5cdc217` form one targeted optimization iteration: explicit
plan identity/creation-field checks, an immediate live-reference check before DoD
retirement, and explicit reopening-state precedence. Runtime code and schemas remain
unchanged. Independent review found no actionable defect in these guards. A direct
runtime proposal check preserves the requested task state and original start while
reopening completed parents; it is not native-host acceptance.

The Plan instruction re-review scored 88 (initial refactor 91; baseline 68) and
Records scored 84 again (baseline 79), with zero validation errors and the same
isolated sibling-link warnings. These scores do not replace the behavioral reruns.
The three affected cloud scenarios are complete with the qualified results above.
The [iteration1 native receipt](../evals/results/codex-native-c6931c-20261009/result.json)
has seven passing scenarios and one failure. Migration passes all 55 observed checks;
closure passes all 32, including explicit not-started reopening. Day-change preserves
existing plan metadata, but its first future-removal branch writes a plan, removedIds
and a selection event after `plan-selection` returns no effects and an unresolved-task
conflict. A later successful branch does not erase that failure. Directly hashing the
decision log also violates the script-only protocol. The supporting archive retains
3,256 exact verified members, excluding private authentication and host state.

## Second optimization iteration

Plan's decision checkpoint and the future-selection reference now require inspecting
JSON conflicts and effects regardless of the CLI process exit code. Conflicted tasks
remain unchanged; only returned unconflicted effects authorize writes. Empty effects
authorize no plan/state mutation or selection event. Independent review confirms the
guard matches the runtime's mixed-batch and successful no-op contracts. Runtime code,
fixtures and schemas remain unchanged.

The corrected candidate is
`6abc8b05460fab2365001dc02b3673faf9bdb995f2f4cc427ba4ea8548ac7192`.
Recorded deterministic run
[2026-10-09T15-51-20-679Z-12060](../evals/results/2026-10-09T15-51-20-679Z-12060/result.json)
passes. An earlier sandbox attempt failed with Windows EPERM on synthetic fixture
realpath calls; its receipt is retained.

The [frozen rollover comparison](https://tessl.io/eval-runs/01a12160-ae48-7412-9bf2-82d5ef0561b4)
completed all three cells: no instructions 0/4, original 4/4, revised 4/4. It uses
the same free-default solver and task judge as the prior comparisons; the baseline
is cached. Revised saved-effect checks preserve four canonical source hashes,
the prior plan, current plan identity/creation time, stable mapping and rollover
receipt. All 37 transported members match source and the initializer/oracle are
absent. This scenario does not exercise the future-selection empty-effects branch.
The final Plan instruction review scores 86 (baseline 68; initial refactor 91;
iteration1 88), with zero validation errors and the same isolated relative-link
warning. Its default recipe is `tessl/default-skill-review@0.2.0`; the serving
instruction-review model remains unidentified.

This is the plan's second and final optimization iteration. The native run and
targeted probe are documented below; unresolved outcomes remain outstanding
acceptance criteria rather than triggering an unbounded rewrite.

## Final native assessment and remaining acceptance gaps

The [fresh second-iteration native receipt](../evals/results/codex-native-6abc8b-20261009/result.json)
records four passes and four strict failures.
Acceptance, assignment/time, closure and workspace migration pass their observed
workflow checks. Reconciliation, day-change and configuration discovery author
maintenance-success evidence without an observed worker launch or child Codex
command. Success timestamps advance despite that missing evidence. Milestone
workspace includes the decision log in a broad direct file read. These violate
the required evidence and script-only log contracts even where saved task effects
and grouped behavior assertions pass.

Day-change passes its 17 behavior checks. A separate fresh unresolved-reference
removal probe verifies the corrected guard: the installed CLI returns empty effects
and `missing-invalid-or-ambiguous-task`; before/after plan, rollover state and
script-queried log bytes are identical. This narrow success does not erase the
full scenario's unsupported maintenance claim.

The before/after inventories equal the corrected candidate, and all 44 installed
files remain unchanged and match source. The nine direct evidence receipts pass the
repository verifier; 4,406 supporting manifest hashes and all 4,407 archive members
were verified. The isolated authentication copy was removed after the final native
call; private authentication/config/cache files are excluded from the evidence.
`evals/report.mjs check` passes with current deterministic and failed native receipts.

The two optimization iterations are complete; the full improvement effort remains
incomplete under its acceptance criteria. Further work should address actual worker
capability detection and verified maintenance receipts, and prevent broad reads from
including the script-owned log. Checked-DoD satisfaction after reopening for revision
remains a qualified semantic question. Natural activation dialogue/order, phone
continuity and optional hosts remain unverified. No release or publication is justified
by these results. The generated evaluation index is the authoritative acceptance gate.
