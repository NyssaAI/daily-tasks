# Daily Tasks

Personal task management and daily planning through six agent skills. Maintain
projects, milestones, tasks and external blockers in editable Markdown; review your
own and delegated work in a local-day plan. Skills provide capabilities to your agent,
without becoming an autonomous assistant persona or fitting work into a timeframe.

## Use

Ask to set up Daily Tasks, capture possible work, update a task, plan the day, or check in.
The router loads only the selected procedure. New projects, milestones and tasks need
explicit acceptance; your instruction to create named work supplies that acceptance.
Quoted requests and inferred promises remain candidates. A check-in can happen anytime; it creates today's missing plan,
carries unfinished selected work forward and reconciles manual checkbox edits.

| Skill | Purpose |
| --- | --- |
| daily-tasks | Route a request |
| daily-tasks-setup | Identity, timezone, priorities and explicit storage scope |
| daily-tasks-capture | Candidate review and explicit acceptance |
| daily-tasks-records | Accepted work, delegation, progress, DoD and blockers |
| daily-tasks-plan | Daily selections, ownership review and explicit future planning |
| daily-tasks-checkin | Reconciliation, progress reports and resumable decisions |

These six skills form the minimal composition: the router selects or combines sibling
workflows, and each child can also activate directly. Shared references, templates and
the Node CLI support those skills. The portable CLI is executable support, not an
autonomous command component. Requested workflows retain stale-on-demand correctness.
OpenClaw users may separately install a thin native adapter that registers an optional
deterministic prewarm command job; no hook, background agent or MCP server is required.

## Storage and authority

- Preferences: partial version-2 layers at `<vault root>/.nyssa-ai/daily-tasks/profile.json`
  and `~/.nyssa-ai/daily-tasks/profile.json`. Project leaves override user defaults;
  omission inherits and documented null leaves select packaged defaults. Reuse accepted
  explicit pointers and legacy `.nyssaai`/`.nyssa` profiles without automatic migration.
  Portable `.` and `./...` paths resolve against the explicitly
  captured vault binding; `~/...` resolves against the current host's home directory.
- Operating state: `<vault root>/.nyssa-ai/daily-tasks/`, independent of shared
  preferences. Content-based discovery preserves existing completed and pending legacy
  state; divergent stores require reconciliation. Reuse a verified established binding.
  Preserve configurationSources and vault/home/state roots through continuation.
- Personal setup needs no vault or decision-log entry. Project bindings and outputs
  remain vault-specific; project preference updates retain their existing decision log.
- Project inventory: `<vault root>/.temp/daily-tasks/project-index.json`. It is disposable,
  refreshed on request or when source checks, local-day rollover or the configurable
  four-hour TTL require it. Cache reuse reads file metadata and no Markdown contents.
  `src/cli/warm-project-index.mjs` resolves configured context and invokes that same
  stale-on-demand path without forcing a rebuild or returning the full inventory.
- Decision log: `{projects root}/.daily-tasks/yyyy.mm.dd-decisions.json`; date means
  file creation. Append-only logical history, script-only access, explicit rotation.
- Daily plans: `{vault root}/2-areas/daily-plans/yyyy.mm.dd-daily-plan.md` by default.
- Project index plus `m1-name/m1-name.md` milestones and sibling `t1-name.md` tasks.
  Each milestone and task owns its own Definition of Done; tasks also own requirements.
  Flat milestone `inputs/` and `outputs/` hold files linked by tasks. Navigation follows
  project -> milestone -> task -> files. Project-wide blockers stay in `blockers/`.
  All local work stays in the project, including `.temp/` scratch. Existing records
  remain readable; [migration](skills/daily-tasks/references/workspace-migration.md)
  converts them on request while preserving identity and history.
- UUIDv7 document IDs use frontmatter `id`; legacy hidden IDs remain readable.
  DoD criterion IDs and projection `ref` IDs use hidden comments. Wiki links use readable labels.
- Store GMT, present configured local time with timezone. Human email owner; optional
  person/agent assignee, falling back to owner. Target dates are optional and explicit.

PARA/file-management conventions are optional and configurable. No plugin cache imports,
mandatory Personal CoS bootstrap, cloud account or external task-service dependency.
`document-maturity` is separate from each record's operational state.

An ordinary folder can be your workspace; no PARA or Obsidian vault is required.
Personal preferences alone use your home directory without asking for work storage.
When you first manage work, setup reuses known locations or asks where to keep the
workspace, project records and daily plans. It can use an existing PARA layout;
otherwise it offers `projects/` and `daily-plans/` in your chosen workspace without
creating a PARA structure.

## Runtime and packaging

You can provide Markdown templates or completed examples for project indexes,
daily plans, milestones and tasks. In a recognized PARA vault, setup or first use
places missing active templates in the vault's Resources/templates folder, using
its existing directory names, and links those editable files. The plugin reads
registered files on subsequent use and preserves explicit existing template paths.

For a supplied example, ask the agent to use it as your template. It stores the
preference in your existing profile and uses it for new documents. Each format
can be customized independently, including the interactive planning review screen.
Existing documents are reformatted only on request.
See [custom templates](skills/daily-tasks/references/templates.md).

Plugin updates and template choices are independent. On the next relevant request,
the agent compares a changed template, offers a preview, and lets you use the new
layout, keep the current revision, or postpone. The default is **Ask about updates**;
you can explicitly select **Always use latest** for compatible updates or **Keep
current** for each template kind. Declining one revision does not change that policy.
Comparisons retain the original bundled version alongside your edited template.
Accepted upgrades update the visible file after checking for intervening edits.
The layout applies to new documents; reformatting today's plan is a separate choice.
See [template updates](skills/daily-tasks/references/template-updates.md).

The planning review shows owned work, preserves stable numbered choices, and offers
one project per page, with ordered additions from its first incomplete milestone. Future
selections use dated daily-plan files and disappear from today's available additions.
The person chooses execution order. See [planning flow](skills/daily-tasks/references/planning-flow.md).

Node.js 22 or later is required for log operations and integrity checks. No npm packages
or credentials are required. Skills need a host that can read/write the selected files
and execute Node. Without those capabilities, proposals are possible but persistence
is unavailable. This is not a task scheduler or a full task database engine.

```text
node src/cli/daily-tasks.mjs --help
node src/cli/daily-tasks.mjs new-id
node src/cli/daily-tasks.mjs log-query --input /absolute/query.json
node src/cli/warm-project-index.mjs --vault-root /absolute/vault --home-root /absolute/home
```

See [CLI contract](skills/daily-tasks/references/cli.md), [record conventions](skills/daily-tasks/references/records.md)
and [reconciliation](skills/daily-tasks/references/operations.md).

Install a host bundle from the [latest release](https://github.com/NyssaAI/daily-tasks/releases/latest),
or build from source with Node >=22 and `npm run assemble`. Generated bundles and
dot-prefixed directories are not tracked in Git; a source checkout must be assembled
before host installation. `npm test`, `npm run check`, and `npm run eval` assemble automatically.
`artifacts/portable` contains the
portable/Codex/Claude/Cursor bundle, `artifacts/cowork` relocates the executable for
Cowork, and Antigravity/Hermes have their own thin adapters. `artifacts/openclaw-native`
is a separate optional OpenClaw adapter. After installing it, project setup can reconcile
a silent hourly command automation with:

```text
openclaw daily-tasks setup-prewarm --vault-root /absolute/vault --home-root /absolute/home
```

Use `--every 30m` (or another OpenClaw duration) to configure the interval and
`--dry-run` to inspect the declaration. The job runs exact Node argv with no model,
agent or chat delivery. Disabling or deleting it only removes the latency optimization;
every consumer still checks staleness on demand. Register the appropriate package
through the host's supported plugin flow. A directory or manifest alone does not
activate it. [Evaluation coverage](evals/LATEST.md) records remaining runtime checks.

For Codex Windows with phone access, the Windows app runs the plugin and accesses the
vault; the phone connects to that host. Native activation and remote pairing need
host verification. `timezone: "system"` resolves the Windows host's timezone.

## Verification

```text
npm test
npm run check
npm run eval
node evals/report.mjs write
npm run eval:check
```

`npm test` also saves the TAP output and a summary to
`test/results/YYYY.MM.DD-test-result-summary.md`, replacing that date's file on
subsequent runs.

Canonical procedures and templates live under [skills/](skills/).
[Evaluation](evals/LATEST.md) records deterministic checks and native-host evidence
for each frozen candidate. Release acceptance requires current passing evidence
for Node and Codex on Windows x64. Other hosts and phone continuation remain
unverified.
