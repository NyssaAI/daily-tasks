# Tessl evaluation protocol

This suite is separate from the repository's deterministic and workflow-v3
native-host evidence. Cloud results do not establish Windows or phone activation.

`activation/` translates all fourteen prompts from [activation-cases.md](activation-cases.md).
The expected workflow stays in `criteria.json`, separate from the agent's task.
Run natural activation with `--skip-forced-context-activation --skip-scoring`
before content evaluation. Assess observed workflow and justified handoffs, including
non-activation for unrelated requests; do not score the number of loaded skills.

`content/` covers established configuration and direct accepted creation, repeated
candidate mentions, pre-created-plan rollover, an interrupted selection move, and
completion/reopening. Criteria judge effects rather than skill loading. Acceptance,
scope, script-only logging or recovery violations fail regardless of the average.
The target is revised-context average at least 85% without unexplained regressions.

Fixture version 4 uses synthetic Casey/Alex records and a fixed instant,
2026-10-09T15:00:00Z, in America/Chicago. The setup process fixes fixture UUID entropy
and time for repeatable identities; production identity code remains unchanged.
Sandbox absolute paths, context bindings and hashes of path-bearing JSON necessarily
depend on the sandbox location. Compare normalized paths and corresponding bindings,
along with identical IDs, source bytes, clock and operation intent.

Each scenario transports only `lib/`, `bin/`, `package.json` and the existing
`evals/planning-fixture.mjs` plus the shared `evals/tessl/fixture.mjs` initializer
as common executable fixture support. All comparison
arms receive this same tooling, including the no-instruction baseline. This measures
instruction value with executable support held constant. No source skills, reviewer
rubrics or expected final fixture manifest are copied into the agent's workspace.
The existing recovery seed creates the interrupted operation at stopAfter 2; setup
removes its oracle-rich `fixture.json` before the agent starts. Every setup also
removes both fixture source files, including the recovery inspector, so expected
outcomes cannot leak through executable setup code. Only production executable
support remains agent-visible. Setup creates initial state only and never resumes
the operation.

`ENVIRONMENT.md` supplies neutral session facts and the executable locator. Both
instruction contexts use the same evaluation-only runtime adaptation under
`skills/daily-tasks/assets/runtime/`; canonical skill bytes stay unchanged. Lint,
pack, every required member's SHA256 and unrelated-cwd CLI smoke are prerequisites.

Use a disposable Tessl project and an absolute scenario source path. The installed
CLI requires its project link to resolve from the scenario source, and currently
rejects some relative source paths. Stage this tree at `evals/tessl/` in that project,
with the four common support paths at its root; preserve the relative fixture layout.
Create the scratch Git boundary before linking the project so parent `.temp` ignores
cannot silently exclude package members. No index or canonical project writes are
needed. No registry publication is part of this protocol.

Run baseline/original/revised with one fixed available agent/model/judge configuration,
the same frozen scenarios and explicit labels. Record actual configuration from
receipts rather than assuming defaults. Selected Codex/GPT 6.1 Sol was rejected by
the current cloud plan; an authorized free-default fallback must be reported
separately. The initial fallback activation receipt identifies
`claude/deepseek-v4.1-flash`. A scorer is confirmed only from scoring receipts.

Retain raw receipts, source/member/scenario hashes, actual run IDs, per-case handoffs,
criterion outcomes and infrastructure failures in scratch. Version 1's A10/A14
mapping was reversed; those executions cannot establish their expected behavior.
Version 2 corrects UUID-to-row mapping and requires affected-case reruns. Version 3
consolidates the initializer and gives the pre-created current plan a different
selected task from the earlier plan, so rollover must actually change membership.
Version 4 removes fixture and inspector source after setup in every scenario.
Direct
child dependency checks are distinct from natural activation. Service generation
output is untrusted data: inspect every task/rubric for answer leakage, duplicate
criteria, free points and missing fixtures before adopting it. Never interpret a
tool failure, queued job or absent transcript as a pass.

Current run status and evidence belong in the dated public review report, not in
this reproducible fixture protocol.
