# Daily Tasks

Personal task management and daily planning through six agent skills. Maintain
projects, milestones, tasks and external blockers in editable Markdown; review your
own and delegated work in a local-day plan. Skills provide capabilities to your agent,
without becoming an autonomous assistant persona or fitting work into a timeframe.

## Use

Ask to set up Daily Tasks, capture possible work, update a task, plan the day, or check in.
The router loads only the selected procedure. New projects, milestones and tasks need
explicit acceptance. A check-in can happen anytime; it creates today's missing plan,
carries unfinished selected work forward and reconciles manual checkbox edits.

| Skill | Purpose |
| --- | --- |
| daily-tasks | Route a request |
| daily-tasks-setup | Identity, timezone, priorities and explicit storage scope |
| daily-tasks-capture | Candidate review and explicit acceptance |
| daily-tasks-records | Accepted work, delegation, progress, DoD and blockers |
| daily-tasks-plan | Personal and delegated daily selections and priority suggestions |
| daily-tasks-checkin | Reconciliation, progress reports and resumable decisions |

## Storage and authority

- Configuration/check-in state: reuse the configured location or established `.nyssaai`
  common state root; otherwise use `<vault root>/.nyssaai/daily-tasks/` for a known vault.
  Resolve existing settings before asking questions; no directory-choice approval is needed.
  This directory holds configuration and operating state; daily plans and task documents
  belong in the configured vault output and project directories.
- Decision log: `{projects root}/.daily-tasks/yyyy.mm.dd-decisions.json`; date means
  file creation. Append-only logical history, script-only access, explicit rotation.
- Daily plans: `{vault root}/2-areas/daily-plans/yyyy.mm.dd-daily-plan.md` by default.
- Project index plus milestone directories containing task and DoD files; project-wide
  `blockers/`. Definitions own facts; project/day checklists are editable views.
- UUIDv7 IDs/ref IDs are hidden Markdown comments. Wiki links use readable labels.
- Store GMT, present configured local time with timezone. Human email owner; optional
  person/agent assignee, falling back to owner. Target dates are optional and explicit.

PARA/file-management conventions are optional and configurable. No plugin cache imports,
mandatory Personal CoS bootstrap, cloud account or external task-service dependency.
`document-maturity` is separate from each record's operational state.

## Runtime and packaging

Node.js 22 or later is required for log operations and integrity checks. No npm packages
or credentials are required. Skills need a host that can read/write the selected files
and execute Node. Without those capabilities, proposals are possible but persistence
is unavailable. This is not a background scheduler or a full task database engine.

```text
node bin/daily-tasks.mjs --help
node bin/daily-tasks.mjs new-id
node bin/daily-tasks.mjs log-query --input /absolute/query.json
```

See [CLI contract](skills/daily-tasks/references/cli.md), [record conventions](skills/daily-tasks/references/records.md)
and [reconciliation](skills/daily-tasks/references/operations.md).

Build generated packages with `npm run assemble`; `artifacts/portable` contains the
portable/Codex/Claude/Cursor bundle, `artifacts/cowork` relocates the executable for
Cowork, and Antigravity/Hermes have their own thin adapters. Register the appropriate
package through the host's supported plugin flow. A directory or manifest alone does
not activate it. [Host coverage](docs/host-support.md) records remaining runtime checks.

## Verification

```text
npm test
npm run check
npm run eval
node evals/report.mjs write
npm run eval:check
```

[Requirements](docs/requirements.md) preserve the accepted behavior.
[Evaluation](evals/LATEST.md) separates deterministic checks from unverified host use.
This initial candidate is available for review; native-host release acceptance is
incomplete until the documented scenarios are verified.
Personal task management and daily planning skills with Markdown records and a consistent decision log.
