# Tessl instruction and security review receipts

These are independent review receipts, not workflow-v3 host results. The dated
[review report](../../../docs/2026-10-09-tessl-guidance-review.md) separates their
scores and limitations from activation, task execution and native acceptance.

`*-before.json` covers canonical instructions at
`d20b74b2ff5d85e064bea890c89e9fe9cf6b057e`. `*-after.json` covers the revised
canonical instructions through `942a990`. Later commits add evaluation fixtures
without changing those instruction bytes. The review plugin is
`tessl/default-skill-review@0.2.0`; these receipts do not expose the serving judge
model, so exact model equality is unverified.

`daily-tasks-plan-iteration1.json` and `daily-tasks-records-iteration1.json` cover
the later behavior-driven instruction corrections. Scores are 88 and 84 respectively.
The original refactor receipts are retained rather than overwritten.

`*-security.json` contains the six security results. The router submission included
the evaluation wrapper's runtime assets; child submissions cover their own skill
directories. These do not represent a single full-wrapper security review.

Original responses are preserved as JSON, with file encoding normalized to UTF-8.
Individual-skill relative-link warnings are retained. Archive membership was
verified separately; missing sibling context in a review upload does not establish
that the complete shipped package lacks those references.

## Cloud task and activation receipts

`cloud/` retains completed initial and iteration1 criterion summaries with the
original judge reasoning, solution identifiers and supported recipe metadata. The
solver is claude/deepseek-v4.1-flash and task judge claude/claude-sonnet-4-6; explicit
Sol selection was rejected by paid-model entitlement. This identity evidence does
not identify the instruction-quality reviewer model.

Initial clean totals are baseline 14/20, original 19/20, revised 19/20; iteration1
affected totals are 7/12, 12/12 and 11.7/12. Baseline iteration1 cells reuse cached
initial controls. Raw fractional scores and disputed deductions are preserved.
The report adjudicates start retention separately from checked-DoD uncertainty.

Natural/direct-entry saved-effects inspections, repeatable fixture QC, source
inventories and recovery oracle outputs accompany the scores. They contain
synthetic records and inspection paths, not personal records or credentials.
Paths identify the original local/cloud inspection roots; they are not portable
execution instructions. Downloaded final files cannot prove dialogue/tool order.
Earlier natural source exposure, invalid initial mapping, invalidated overlay run
and initial faulty recovery normalization remain disclosed in the report.

`recovery-revised-oracle.json` is the initial faulty normalization receipt;
`recovery-revised-oracle-v2.json` supersedes it. Iteration1 oracle receipts inspect
untouched downloaded JSON with rebased locators and actual-root expected hashes.
No full workspace archives or authentication output are published here.

Iteration2 stages frozen candidate
`6abc8b05460fab2365001dc02b3673faf9bdb995f2f4cc427ba4ea8548ac7192`
(committed correction `54bd411`) with the same four rollover fixture files and
37 verified packaged/transported source members. Plan instruction review
`daily-tasks-plan-iteration2.json` completed at 86 with zero errors and one sibling
link warning; the receipt confirms `tessl/default-skill-review@0.2.0`. Explicit
selection of that plugin was rejected by paid entitlement, so the unchanged
default recipe was used. Serving instruction-review judge remains unidentified.
The rollover task comparison retains separate receipts and cached baseline;
no five-case aggregate is inferred from this one-case rerun.

Iteration2 rollover run `01a12160-ae48-7412-9bf2-82d5ef0561b4` completed three
cells: baseline 0/4 (cached initial solution), original 4/4, revised 4/4. Supported
recipe metadata confirms solver `claude/deepseek-v4.1-flash` and judge
`claude/claude-sonnet-4-6`. `cloud/iteration2-content-summary.json` preserves exact
criteria and reasoning. `cloud/iteration2-saved-effects.json` verifies four
canonical source hashes, the previous plan hash and all 37 transported members;
current plan identity/creation is preserved, carry occurs once, and the stable
review mapping/rollover receipt is saved. Initializer/oracle sources are absent.
This rollover case does not trigger future-selection's empty-effects branch.
Final files cannot establish full dialogue or ordered tool calls.
