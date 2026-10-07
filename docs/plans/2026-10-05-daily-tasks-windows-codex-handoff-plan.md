---
artifact_contract: "ce-handoff/v1"
created_at: "2026-10-05T19:12:35Z"
title: "Daily Tasks implementation handoff to Windows Codex"
summary: "Resume the implemented local daily-tasks candidate, complete review and independent evaluation, and deliver coordinated plugin, PARA, and marketplace changes."
keywords: ["daily-tasks", "windows", "codex", "implementation", "handoff"]
cwd: "D:/repos/NyssaAI/daily-tasks"
resume_focus: "Finish verification and delivery of the agreed public plugin without repeating product discovery."
repository: "NyssaAI/daily-tasks"
repo_root_sha: "667ff5045aebbe85ad56d43b4f954eed3358d320"
branch: "feat/initial-plugin"
head: "11fd3dcd60e88dea6d9c882b22a9bcad4b8ba8b6"
---

# Daily Tasks — implementation continuation plan

## Goal and latest user intent

The user authorized implementation of the new public `NyssaAI/daily-tasks` plugin
after a detailed design conversation. The latest request is to create a detailed plan
in `docs/plans/` so the Windows app version of Codex can take over this work.
This document is the transfer checkpoint, not a declaration that delivery is complete.
The receiving session should orient, verify the local state, and obtain the user's
continuation direction before acting on this handoff. Product decisions below were
accepted by the user; implementation choices are called out separately.

## Critical continuity warning

**Open the existing Windows checkout at `D:\repos\NyssaAI\daily-tasks`. Do not start
from a fresh GitHub clone.** Most code is only in the local working tree/index.
GitHub currently has the initial README commit on `main`, not the implementation.
The local feature branch has one additional committed requirements/interface baseline;
the code is staged, with later fixes also unstaged. Staged content is older than the
working tree in several files. Do not discard either side or commit only the old index.

No commit, stash, branch teardown or publication was performed merely to create this
handoff. Retain all three local checkouts. If the Windows app cannot access the same
filesystem, transfer the working directories including their Git state or deliberately
publish a reviewed checkpoint; copying only this document or cloning remote main is
insufficient. There is no managed temporary duplicate of this handoff.

## Repository state at capture

Paths in this table are machine-local, not portable plugin settings.

| Repository | Local checkout | Branch | HEAD | State |
| --- | --- | --- | --- | --- |
| daily-tasks | `D:/repos/NyssaAI/daily-tasks` | `feat/initial-plugin` | `11fd3dcd60e88dea6d9c882b22a9bcad4b8ba8b6` | Requirements baseline committed; substantial staged implementation plus unstaged fixes and review receipt |
| agent-skills | `D:/repos/NyssaAI/agent-skills` | `feat/document-maturity` | `a3d4e98f8d19a8705646d4ebc568142d5cf2296b` | Clean before task; 25 tracked files changed for PARA rename/version/evals; uncommitted |
| plugin-marketplace | `D:/repos/NyssaAI/plugin-marketplace` | `feat/daily-tasks-listing` | `ee74333fc90cdb3b89a5472e32956ca7fb0b73a1` | Two catalogs and README updated; uncommitted |
| plugin-builder | `D:/repos/NyssaAI/plugin-builder` | `main` at entry | Existing private repository | Read-only guidance; no implementation changes made |

Public remote created: https://github.com/NyssaAI/daily-tasks.
Remote main: `667ff5045aebbe85ad56d43b4f954eed3358d320`.
No feature branch push or open PR exists for any of these three changes at capture.
Nothing has been merged, tagged, released, or installed into a personal profile.
No actual user vault/configuration was changed. Tests use synthetic data under `.temp/`.

## Read these artifacts first

1. [Requirements](../requirements.md): R1–R15 preserve accepted behavior and the
   implementation-unit outline. Treat the user's choices as settled, not open ideation.
2. [Executable contract](../executable-contract.md): the module/API boundaries and
   JSON-safe before/after presence snapshots added in the latest fix.
3. [Repository instructions](../../AGENTS.md): canonical skill tree, no persona,
   no automatic scheduling, narrow JavaScript scope, explicit filesystem roots.
4. [Record conventions](../../skills/daily-tasks/references/records.md): data layout,
   metadata, IDs/links, closure/reopening and timing semantics.
5. [Operations protocol](../../skills/daily-tasks/references/operations.md): per-view
   reconciliation baselines, pending checkpoints, log ordering and recovery.
6. [CLI reference](../../skills/daily-tasks/references/cli.md): actual commands, effects,
   log access contract and current performance limitations.
7. [Adversarial receipt](../2026.10.05-plugin-review-adversarial.md): independent
   baseline findings ADV-001/002. Fixes exist locally, but independent delta review is pending.
8. [Development receipt](../2026.10.05-plugin-review.md): implementation/simplification
   evidence. Its "35 tests" describes the pre-fix run; capture now has 37 passing tests.
9. [Evaluation contract](../../evals/README.md), [matrix](../../evals/matrix.json),
   [latest report](../../evals/LATEST.md): distinguish code tests from host behavior.
10. [Host coverage](../host-support.md): generated adapters, activation routes and gaps.

Additional machine-local references:

- `D:/repos/NyssaAI/agent-skills/AGENTS.md`: its `docs/` is private/ignored; never
  force-add its review or planning documents.
- `D:/repos/NyssaAI/agent-skills/docs/para-maturity-verification.md`: related unit's
  baseline and final commands, compatibility decisions and test results.
- `D:/repos/NyssaAI/plugin-builder/skills/plugin-builder/SKILL.md`: build method.
  Its `agents/adversary.md` and `agents/eval.md` govern independent final gates.
- `C:/Users/jmayn/.codex/plugins/cache/jamaynor/compound-engineering/3.30.3/skills/ce-work/SKILL.md`:
  execution/shipping workflow already selected; native engine, no external implementation model.
- Same skill root's `ce-code-review`, `ce-simplify-code`, `ce-commit-push-pr` and
  `ce-handoff` instructions as applicable. Read required references, not guessed summaries.
- `C:/Users/jmayn/.codex/plugins/cache/jamaynor/dev-standards/3.24.2/skills/dev-standards/SKILL.md`:
  development baseline already applied.

## Accepted product boundaries — do not reopen them casually

### Purpose and authority

- Name `daily-tasks`, public repository under NyssaAI. Personal plugin viewed from
  configured user's perspective. Task management and day planning are separate skills
  within one plugin. An agent coordinates; skills provide capabilities, not a persona.
- Never fit work into available time, calculate capacity, allocate calendar slots, or
  require every open task to be scheduled. Prioritization suggestions are allowed and
  explain their basis in explicitly configured priorities. Priorities never silently change.
- One authoritative record per tracked item. Markdown project and daily checklists are
  editable views; direct edits of existing items reconcile into authoritative records.
- New tasks/projects/milestones must be created through skills after explicit human
  acceptance. Batch acceptance is valid. Manual new checkbox becomes a candidate.
- `owner` is always a human email, default configured current user; only a user can
  designate/change it. `assignee` is optional human email or stable named agent, assignable
  by human or agent. Absent assignee means owner does the work, no unassigned category.

### Records and storage

- UUIDv7 for everything tracked, including DoD criteria; hidden `id`/`ref` comments.
  Raw source still shows comments. Wiki navigation uses readable names plus hidden IDs,
  reciprocal links maintained; UUID, not filename, preserves identity through moves.
- Project index is Markdown first. Milestone directory directly contains task files and
  DoD; separate project `blockers/`. Task-level DoD is excluded. HTML deferred.
- Configuration: user-selected `.nyssa/daily-tasks/{structure}`. The base of `.nyssa`
  has NOT been configured on the user's machine; setup asks for explicit absolute scope.
- Log: `{projectsRoot}/.daily-tasks/yyyy.mm.dd-decisions.json`; filename date means
  creation, not one file per day. One logical plugin-wide append-only JSON history.
- Daily plan: `{vaultRoot}/2-areas/daily-plans/yyyy.mm.dd-daily-plan.md`.
  Filename uses local calendar day; storage convention remains configurable.
- `document-maturity` replaces PARA `status`. Operational fields are project-state,
  milestone-state, task-state, blocker-state. Optional tags classify, not encode state.
- Optional PARA/file-management conventions can change; no cache-path imports, mandatory
  dependency or CoS bootstrap. Existing personal CoS is prior art, not modified or executed.

### Lifecycle, relations and time

- Project/milestone/task states: not-started, in-progress, completed, cancelled.
  Blocker states: open, resolved. No paused state.
- Dependencies are informational task-to-task prerequisites, never start gates or override
  ceremonies. Cancelled prerequisite remains linked and visibly flagged.
- Blockers usually represent external conditions (approval, access, third-party response).
  A task to request approval can complete while the approval blocker remains open.
  Shared blocker has one authoritative record and can affect several milestones/projects.
- Milestone closure: DoD satisfied, all tasks explicitly completed/moved/cancelled, no
  preventing open blocker. Project closure: milestones completed/cancelled, no preventing
  blocker. Parent checkbox requests validation, never silently finishes children.
- Cancellation of parent requires explicit child dispositions, batch allowed. Cancelled
  tasks stay visible struck through and labelled Cancelled; they are not checked completed.
- Reopened task automatically reopens completed parents. Unchecking completed task maps
  to in-progress if a start was recorded, otherwise not-started. Reopening DoD/blocker
  reopens affected completed parents without undoing completed tasks.
- Cross-project moves preserve identity/history/state/relationships/owner; unresolved
  incoming tasks reopen completed destinations. Removed old membership counts as moved.
- Timing: created_at, updated_at, optional started_at/resolved_at/target_date. No deadline
  or review_on. Optional target_date is explicit, never inherited/calculated.
- Start requires explicit report/action, including retrospective. Keep activity and
  recording times. Unclear event time uses current time and retains original wording and
  fallback indication in log. Same rule for completion/cancel/blocker resolution.
- Store timestamps GMT ISO ending Z. Display local timezone always explicitly named.

### Daily planning and consistency

- Setup captures identity/email, IANA timezone and explicit priorities.
- Daily plan separates own and delegated work; owner fallback handles omitted assignee.
- Check-in anytime. If today is missing create only today, not skipped days. Carry unfinished
  selections from latest earlier plan automatically. Completed/cancelled stays visible on
  its day but doesn't carry. Explicit removal keeps task open and stops future carry-forward.
- Conflicts block only affected items. Unambiguous interrupted operations repair automatically.
  Missing files preserve refs; deletion doesn't imply lifecycle change. Duplicate IDs need
  explicit disposition; never silently re-ID a copy. Pending decisions resume without repeats.
- Compact decision log is distinct from records, append-only corrections reference originals.
  Script-only access, archives preserve IDs/contents. It is not a full backup of every edit.
- Narrow JS helpers for UUID/time/validation/links/change detection/closure/recovery. Skills
  own document mutation, prioritization, interpretation and acceptance. No central task engine.

## Implementation present now

### Canonical skills and templates

Six `skills/*/SKILL.md` entry points: router, setup, capture, records, plan, checkin.
Router references hold shared records/operation/CLI guidance. Six templates cover task,
milestone, DoD, blocker, project index and daily plan. Relative links are statically checked.
Setup/CRUD/check-in are skill procedures executed by the host, not JS subcommands.

### Executable features

- `lib/identity/identity.mjs`: UUIDv7, timestamp/version/variant validated in tests.
- `lib/log/decision-log.mjs`: strict entry validation, process lock, atomic JSON extension,
  idempotent operation IDs, corrections, query/filter/pagination, immutable archive rotation,
  archived ID reservation, symlink/corruption rejection and dry-run.
- `lib/records/`: scalar frontmatter parser, validation, closure and reciprocal-link checks.
  Metadata supports simple scalars plus tags-only JSON string arrays, not arbitrary YAML.
- `lib/reconciliation/reconciliation.mjs`: pure three-way field merge, ancestor reopening
  and recovery classification. No document writers.
- `lib/time/time.mjs`: strict GMT input, event/record timing, local date and zoned display.
- `lib/planning/planning.mjs`: pure carry-forward and checklist extraction.
- `lib/profile/profile.mjs`: explicit setup-value validation, no profile writer.
- `bin/daily-tasks.mjs`: one-JSON-result CLI, named operations, absolute JSON input-file
  contract, errors on stderr, no cwd-based user scope. Mutation only in logging operations.

### Packaging and evaluation

- Root portable identity 0.1.0 plus generated Claude/Codex/Cursor manifests.
- `scripts/assemble.mjs` writes/checks 138 generated files: portable, Antigravity,
  Cowork (CLI in scripts/), Hermes (Python skill registration shim).
- `scripts/validate.mjs` checks six skill names, internal links and package contract.
- `scripts/write-capabilities.mjs` produces `capabilities.json`; generator parity should
  be included in final review, as current package checker only checks nonempty operations.
- `.github/workflows/ci.yml` runs tests/package checks on Windows, Linux and macOS Node22.
- `evals/` freezes source inventory and keeps raw deterministic execution evidence,
  generates LATEST report, and explicitly fails release acceptance for unverified hosts.

### Related repository changes

`agent-skills` 0.4.0 -> 0.5.0, PARA skill 0.2.0. Canonical references/examples use
document-maturity. Legacy status recognized only for raw/draft/reviewed/established;
conflicting old/new values surface. Existing-note migration needs explicit authorization;
no user notes migrated. Updated C17/C18 eval scenarios, sensitivity test, generated hosts.
Corpus 0.3.0 and suite matrix revision 0.6.0; do not confuse these with plugin version.

`plugin-marketplace` catalogs add daily-tasks 0.1.0 and agent-skills 0.5.0, README agrees.
This is a prepared listing, not live. It references default branches; do not merge listing
before those repositories contain the intended plugin versions on their default branches.

## Verification actually observed

At 2026-10-05T19:12Z, Node v24.19.0 on Windows:

| Check | Observed result |
| --- | --- |
| `npm test` | 37/37 pass after recovery fix |
| `npm run check` | 138 generated files match; six skills and references validated |
| Claude portable manifest validation | Pass before latest code-only fixes |
| Claude Cowork manifest validation | Pass before latest code-only fixes |
| PARA assembly | Generated AGY/Hermes content matched |
| PARA package validator | 60 checks pass |
| PARA unit suite | 33 tests pass |
| PARA eval report consistency | Pass, release still incomplete |
| Marketplace catalog comparison | Five entries agree on name/version/source URL |

Proof-first work observed missing modules, concurrency lock-race regression, JSON absence
round-trip regression and optional-field removal regression before fixes. Final 37 tests
include multi-process log appends, archived corrections/IDs, dry-run, malformed metadata,
template cross-record closure, stale views/conflicts, local midnight/DST and packaged CLI.

`evals/results/2026-10-05T19-07-18-173Z-36116/` is a genuine earlier 35-test deterministic
pass, candidate hash `63dc1e350a6593aa6f5a4c6dec7d40dff6759b695decb7437b4b188347cff43f`.
**It is stale after the fixes.** Existing LATEST.md has not been refreshed since then;
`eval:check` may correctly fail until final evaluation reruns and regenerates it.
Do not delete or rewrite historical evidence or call it the final independent evaluation.

No native plugin discovery/activation or agent workflow has been established by these tests.
Claude Code 2.1.265 is installed but `claude auth status` reported loggedIn false.
Codex CLI 0.160.0 reports ChatGPT authentication available. Antigravity CLI 1.2.14 exists.
Cursor command exists. Other hosts/UI/CPU platforms remain unverified. No credentials
were copied into the repository. Node22 CI has not run because branches aren't pushed.

## Review findings and last changes

### Independent builder adversary

Receipt: [adversarial review](../2026.10.05-plugin-review-adversarial.md).
Its baseline normalized inventory hash is
`6bfe20a5057297f5f044995b0ad2eb4bec883ced5a78ca740446b015db47e12e`.

- **ADV-001 (high):** before/after undefined values disappear through JSON, so a persisted
  recovery checkpoint cannot represent adding an optional field or clearing resolved_at.
  Root implemented explicit presence snapshots and two regression tests. Need independent
  delta review and final CLI-level evaluation of the serialized repair.
- **ADV-002 (low):** Cowork relocates CLI to scripts/ while help advertised nonexistent bin/.
  Root changed help to `node <installed-entry-path> ...`; artifacts regenerated.
  Need reviewer confirmation of both canonical and Cowork help.
- No actionable PARA migration issue found in this review. Runtime gaps remain explicit.

New snapshot convention: `before` / `after` each hold `{present:false}` or
`{present:true,value:...}`. Reconcile output uses `field`; convert to unique recovery
`key`. Actual recovery input is plain key->value. Partial view null requests clearing
optional assignee/target/start/resolution fields; omitted view fields mean no edit.
These changes are UNSTAGED on top of a STAGED older implementation.

### CE code review

A full `ce-code-review mode:agent` was started against staged baseline/current branch.
The handoff request interrupted completion. At capture, correctness and standards
reviewers had returned no findings; testing reviewer was still being collected.
Remaining selected lenses, merge/validator/report had NOT completed. Therefore this
is **not a completed code-review receipt** and does not satisfy the shipping gate.

Machine-local review artifacts:
`D:/repos/NyssaAI/daily-tasks/.temp/ce-code-review/20261005-review/`.
The review agent is writing a partial receipt under docs; inspect for
`2026.10.05-code-review.md` or similarly named partial receipt after opening the checkout.
Do not assume all agent handles will exist in the new app session.

The cross-model peer job was reaped/waited to terminal state; its result was not read or
merged because the review was stopping. Machine-local job path:
`C:/Users/jmayn/AppData/Local/compound-engineering-jobs/ce-code-review/20261005-review/jobs/20261005T190925Z-7c94afcf`.
Automatic approval review rejected its verified-path cleanup as "blocked by policy"
with no more specific reason. Directory may remain. Do not bypass that rejection;
this cleanup limitation does not affect source preservation or test results.

Three simplification reviewers completed. Root reused strict time validation, removed
an unreachable array check, and documented why durable log indexing/parallel scanning
were deferred. Full-history query/append scanning remains linear; archive bounds active
rewrite size but does not eliminate historical scans. Do not promise indexed performance.

## Continuation work, in dependency order

### 1. Re-establish the exact local candidate

Read instructions and references above. Verify each branch, HEAD, staged/unstaged diff,
untracked receipts and pre-existing changes. Preserve everything; no reset/clean/stash.
Confirm no old reviewer or shell process can mutate the same files before editing.
Use the current working tree, not the older staged snapshot, as the code to evaluate.
The tree was clean at original entry, so listed implementation changes belong to this
task; still inspect for any user changes made after handoff before staging.

PowerShell orientation commands (read-only):

```powershell
Set-Location 'D:\repos\NyssaAI\daily-tasks'
git status --short --branch
git log -3 --oneline
git diff --name-only
git diff --cached --stat
git -C '..\agent-skills' status --short --branch
git -C '..\plugin-marketplace' status --short --branch
```

### 2. Finish review and any necessary corrections

Collect the partial review receipt and reproduce actionable findings. Rerun actual
ce-code-review against the completed working-tree candidate, preserving accepted scope.
Don't substitute a mental review or the prior adversarial receipt for its required gate.
Complete builder adversarial delta review of ADV-001/002 and affected requirements.
Keep reviewer receipts immutable; record dispositions in the main review document.

Priority review targets beyond known fixes:

- Round-trip every CLI recovery payload through JSON, including absent vs null and deletion.
- Reconcile DoD criteria and parent checkboxes without accidental implicit closure.
- Ensure per-view baseline instructions are sufficient for a real host to distinguish
  stale rows, explicit removals, changed checkboxes and new candidate rows.
- Ensure the narrow script boundary is preserved; don't solve this by introducing a CRUD engine.
- Verify default owner/user authorization remains distinct from syntax checks in code.
- Verify root manifests, package copies, capabilities and supported artifact paths agree.
- Validate the related PARA diff and marketplace dependency sequencing.

Changes to code require regression proof and regeneration. Do not edit artifacts by hand.
Keep 0.1.0 for this unreleased initial candidate; don't bump for every review repair.

### 3. Verify code and package state

Commands from daily-tasks checkout:

```powershell
node scripts/write-capabilities.mjs
node scripts/assemble.mjs write
npm test
npm run check
claude plugin validate artifacts/portable
claude plugin validate artifacts/cowork
git diff --check
```

No npm install is necessary: package currently has zero external dependencies.
Recheck whether generator rerun changed capability bytes; keep generated content consistent.

For PARA, use existing repository commands (confirm current script help):

```powershell
Set-Location 'D:\repos\NyssaAI\agent-skills'
python scripts/assemble.py check
python scripts/validate.py
python -m unittest discover -s test -q
python evals/report.py check
git diff --check
```

If exact command differs, inspect existing README and private unit receipt; do not invent
a new validation framework. Do not execute migration on actual user notes/cache.

### 4. Run final independent evaluation

Use maintained plugin-builder eval agent in a fresh context after code and adversarial
review settle. Freeze behavior-affecting source/suite inventory and artifact hashes.
Run every available deterministic case, keep failures and unavailable attempts, then:

```powershell
Set-Location 'D:\repos\NyssaAI\daily-tasks'
node evals/run.mjs
node evals/report.mjs write
node evals/report.mjs check
node evals/report.mjs release
```

Release command is expected to remain nonzero while required host scenarios are
unverified. This is separate from a failing implementation test. Do not change the
matrix to manufacture a release pass. The current report generator marks host rows
unverified; if native evidence is newly captured, any report-ingestion enhancement is
a source change needing review and affected evaluation before treating it as final.

Attempt isolated host scenarios from evals/README.md where actual capability permits.
Codex auth exists, but plugin registration must not modify the user's personal profile
without authorization. Use a genuinely isolated supported path; no environment-variable
shell tricks that repurpose HOME/CODEX_HOME. Codex exec --ignore-user-config exists,
but does not alone prove plugin installation isolation or discovery. Claude native test
is blocked by authentication until the user provides a supported connection.
Never expose tokens in command output. Record unavailable hosts honestly.

Also rerun affected PARA evaluation cases C17/C18 through available supported harnesses;
old scores are not fresh evidence for renamed metadata behavior.

### 5. Commit, push and prepare coordinated PRs

After the actual code-review gate, use the established shipping workflow. Inspect both
staged and unstaged changes so the JSON recovery fix is included. Keep ignored scratch,
personal settings, private agent-skills docs, and peer job artifacts out of commits.
This machine-specific handoff is authorized as a local document; consider sanitizing
machine-local paths before public publication rather than publishing unrelated context.

Expected review branches:

- `NyssaAI/daily-tasks`: initial plugin source, canonical skills, generated packages,
  meaningful tests, redacted evaluation results/limitations, requirements and docs.
- `NyssaAI/agent-skills`: document-maturity compatibility change and 0.5.0 metadata.
- `NyssaAI/plugin-marketplace`: daily-tasks listing and agent-skills version update.

The marketplace PR must depend on the other repositories being available at their
listed default refs. Keep it draft/unmerged until that condition holds. Preserve private
plugin-builder listing. CI should run Node22 on Windows/Linux/macOS after push.
Do not merge/tag/release merely to satisfy a handoff; follow current user authorization
and required review/evaluation gates. Source/evidence may be published on review branches
with clearly documented runtime gaps even when full release acceptance is incomplete.

### 6. Report completion precisely

Separate: implementation status, deterministic verification, native-host verification,
publication (committed/pushed/PR/merged), and release readiness. Link actual PRs and
evaluation reports. Do not claim marketplace live until its default branch is updated.
Do not claim personal installation or PARA user-note migration; neither is in this run.

## Completion criteria for the resumed implementation

- Requirements R1–R15 are represented in canonical skills/code/tests without scope drift.
- All concrete review findings are resolved or explicitly dispositioned with evidence.
- JSON recovery fix and packaged help receive independent delta verification.
- Full tests/package checks pass on exact candidate; platform CI results are checked.
- Actual ce-code-review receipt complete; independent builder evaluation runs all
  available cases and records unverified hosts separately.
- Source and retained safe evidence are committed and pushed to the intended public
  review branch; related PARA and marketplace PRs are correctly sequenced.
- User receives accurate links and remaining verification/activation limitations.

## Avoid these false starts

- Do not restart ideation, rename the plugin or ask the dozens of already-settled questions.
- Do not reintroduce capacity scheduling, inferred acceptance, task-level DoD, paused state,
  automatic owner reassignment, duplicate writable authority or a central JS task engine.
- Do not treat all document edits as proof of starting work or all checkboxes as accepted tasks.
- Do not use the installed older PARA cache as the current repo's folder-depth contract:
  fetched source already permits purposeful nesting; the agreed flat layout is still valid.
- Do not infer complete host compatibility from manifests or direct Node tests.
- Do not trust an old LATEST report after source changes or erase failing historical attempts.
- Do not commit only the old staged snapshot, clone away the uncommitted implementation,
  or force-add private agent-skills documentation.
