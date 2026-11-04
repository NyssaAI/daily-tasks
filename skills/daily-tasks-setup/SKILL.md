---
name: daily-tasks-setup
description: Set up or explicitly update Daily Tasks identity, timezone, priorities and storage locations. Use on first use, when project setup is not already done (missing profile.json or workspace configuration), or when the user changes personal planning preferences.
---

# Set up Daily Tasks

Trigger setup whenever project setup is not already done (missing workspace profile or unresolved bindings like `projectsRoot`, `dailyPlansRelative`, `user.email`, or `timezone`), on first use, or upon explicit configuration change requests. If a planning, check-in, or record request arrives before project setup is complete, run this setup workflow first to establish the necessary profile layers before continuing the original request.

Resolve configuration before asking questions. Load the
[MCP / CLI interface](../daily-tasks/references/cli.md) for context/profile/server operations and
[record conventions](../daily-tasks/references/records.md) for output bindings.
Keep the user proactively informed of progress: alert the user clearly as each setup phase executes (checking profiles, detecting runtime/uv, registering MCP server, and setting up templates). Never run silent multi-command probe loops without status feedback.
Use the host's established absolute workspace root or captured initial workspace
binding and verified user home. A nested directory, plugin installation or later
subprocess cwd cannot establish another project. Installation scope never determines
preference scope. Paths passed to tools and scripts are absolute.

## Read and select a write scope

Read both applicable levels: `<userHome>/.nyssa-ai/daily-tasks/profile.json` and
`<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`. Within each level reuse an explicit
accepted pointer; otherwise use canonical `.nyssa-ai`.
Read exact paths without recursively scanning home. Diagnose malformed selected profiles.

Preserve `configurationSources: {schemaVersion: 1, user: {profilePath: ABSOLUTE_PATH_OR_NULL},
project: {profilePath: ABSOLUTE_PATH_OR_NULL}}` unchanged, together with
`workspaceRoot`, `homeRoot` and `stateRoot`, for preparation, save, maintenance and recovery.
Null records deliberate absence. Revalidate those roots on continuation.

Explicit current-task choices override project preferences, which override user
preferences. Pass supported one-off leaves in optional `preferenceOverrides` (without
`schema_version`); preserve them through that request's continuation and never save them.
When home and workspace share storage, `sharedScopes` identifies the aliased
destinations. A stored v2 document can supply both views: user reads use only
preference leaves; binding fields apply only to its selected project view. This
also applies to accepted custom pointers on personal-only or other-workspace reentry.
Validate the complete stored document, then merge only the requested scope's changed
leaves, preserving project bindings and unrelated personal values. Shared preference
changes affect every session using that source; explain this before an update choice.
Independent project overrides need a distinct accepted source, never an automatic move.
Ordinary reads and one-off choices never save preferences. For writes,
reuse an accepted scope. An explicit personal/all-projects request uses user scope,
even in a project session. Otherwise new setup uses project scope when a workspace is
established, and user scope when no project is established. Do not ask routine scope
questions when these rules resolve the destination. A project write needs a resolved
project; personal preference setup needs no workspace or project collection.

Ask only for missing name and email; reuse trusted supplied identity. Default timezone
to `system` and priorities to an empty list without routine questions. Resolve and
report the actual host timezone while persisting `system`; preserve an explicit IANA
zone unless changed. Failed host detection requires an explicit IANA zone, never a
silent UTC fallback. Accepted priorities change only on an explicit request, retaining
the user's reason. Do not fabricate work to complete setup.

## Stored preferences and project bindings

### Establish workspace storage

The workspace is the bound directory. Personal-only setup uses the verified
user home, leaves project configuration absent and asks no workspace/storage question.

When the requested work needs project records or a daily plan, reuse accepted
workspace and output locations first. If no workspace is established, ask where the
user wants to keep that work; their chosen folder establishes the absolute workspace root.
Do not use the plugin installation or an incidental current directory as that choice.
Ask only for unresolved project-record and daily-plan locations, together when both are missing; offer
`projects/` and `daily-plans/` under the chosen workspace as concrete choices.
Persist the selected `projectsRoot` and `dailyPlansRelative` in the project layer and
continue the original request. Explain that daily plans belong inside the workspace;
an explicitly assigned projects collection may be outside it. Preserve existing
bindings, including the packaged daily-plan default when already accepted.

Bundled templates remain usable; user-supplied
templates follow the rules in [custom templates](../daily-tasks/references/templates.md).
Configuration and operating-state locations remain conventional; ask about the
user's work storage, not internal profile/cache/state paths.

Profiles use schema version 2 and may contain only the selected scope's values:

```json
{
  "schema_version": 2,
  "user": {"name": "Example User", "email": "user@example.com"},
  "timezone": "system",
  "priorities": []
}
```

For a project layer, add accepted project bindings, for example `workspaceRoot: "."`
(with `vaultRoot: "."` as an accepted alias),
`projectsRoot: "./1-projects"`, and `dailyPlansRelative: "2-areas/daily-plans"`.
These are project-only bindings, never reusable user defaults. Resolve `projectsRoot`
from an existing accepted collection; ask only if ambiguous. The default daily-plan
output is `2-areas/daily-plans`.

Supported preferences are partial `user.name`/`user.email`, `timezone`, `priorities`,
`templates.projectIndex`, `templates.dailyPlan`, `templates.milestone`,
`templates.task`, `templates.planDayReview`, `projectIndex.ttlSeconds`, and
`sources` (`autoScan`, `directories`, `mcps`, `harnessConnections`, `initialLookbackDays`).
Directories must be workspace-relative
paths without traversal. Scalars and arrays replace; supported object leaves merge.
Template registration, inheritance, resets, and portable paths (`./`, `~/`, absolute)
follow [custom templates](../daily-tasks/references/templates.md). For template
update policies and snapshots, follow
[template updates](../daily-tasks/references/template-updates.md). Do not add unsupported
policy fields to `profile.json`. Retained snapshots/choices live beside that profile under
`templates/updates.json`. They are configuration assets, not workspace operating state.
Registration and template adoption never authorize reformatting existing documents.

Missing project bindings do not prevent personal setup. Do not persist credentials,
private message copies or cache paths. Keep configuration outside installed source.

After workspace configuration resolves, follow
[visible template placement](../daily-tasks/references/templates.md)
for all five template kinds. Proactively place missing active templates in the workspace's
templates directory and record initial baselines. Preserve existing pointers, null resets and
destination files. Link the templates directory and registered files in setup results so the user
can inspect/edit them. Personal-only setup needs no workspace templates.

## Operating state and output

Configuration contains `profile.json` and optional templates. State contains workspace-local
pending operations, completed rollover/removal history, candidates, review progress
and reconciliation baselines. Daily Markdown plans and project records belong to their
resolved output roots, never below either configuration root or state storage.

State uses canonical `<workspaceRoot>/.nyssa-ai/daily-tasks/` unless an explicit
`stateRoot` is supplied and matches established history. Divergent stores require
explicit reconciliation before writes. Never combine stores or select by modification time.
A preference-scope change never authorizes moving state or outputs.

Report changed settings and their path. **Personal setup and updates complete without
a project decision-log entry**, even in a workspace session; never replay them into a
later project log or create a separate audit system. Report resolved timezone and separate
configuration/state/output roots when applicable. Create state only when needed.
Setup authorizes no work creation or ownership changes. When reached
from another request, continue that already-authorized work after resolving its scope.

## MCP server and connectors

Setup must verify or register the planning MCP server in the host configuration so native `daily_tasks_*` tools are available.

### Runtime detection (`uv` and `python`)
Detect the execution environment using fast, single-step path lookups:
- Check for `uv` using `where.exe uv` (Windows) or `which uv` (POSIX). **NEVER scan directories recursively across the filesystem for `uv.exe`**.
- If `uv` is found: use `uv run daily-tasks-mcp` or `uv run python -m daily_tasks.server`.
- If `uv` is missing: alert the user. Explain that `uv` is recommended for fast virtual environment management (can be installed via Astral: `powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows or `curl -LsSf https://astral.sh/uv/install.sh | sh` on Unix), but setup will proceed using host `python` (>= 3.12) with `PYTHONPATH` pointed to `<pluginRoot>/src`.

### Host MCP server registration
Register or update the MCP server in the host agent:
- For Antigravity / Gemini CLI: run `agy mcp add` or add to `~/.gemini/config/mcp_config.json`:
  - With `uv`: `agy mcp add daily-tasks uv run --directory <pluginRoot> daily-tasks-mcp`
  - With host Python: `agy mcp add --env "PYTHONPATH=<pluginRoot>/src" --env "DAILY_TASKS_LOG_LEVEL=Debug" daily-tasks python -m daily_tasks.server`
- Confirm MCP server registration and tool readiness to the user.

The planning MCP server runs over stdio as `daily-tasks-mcp` (or
`python -m daily_tasks.server`) from the plugin root. It must ONLY be used via MCP tool calls;
agents must never invoke it as a CLI command. Pass absolute
`--workspace-root` (or rely on the workspace root cwd); it reuses `user.email`,
`user.name`, `timezone`, `projectsRoot` and `dailyPlansRelative` from
`<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`, so ask only
for values that are missing (`--user-email`, `--timezone` override them). Stdout carries
only MCP JSON-RPC; logs go to stderr (`DAILY_TASKS_LOG_LEVEL`, optional `--log-file`).

### Communication sources and initial lookback

Before offering any standalone credential setup, check which email (Gmail, Outlook, ...) and chat
(Slack, Teams, ...) connections the host already provides (Claude, Codex, Antigravity, Cursor):
list the host's connected integrations and MCP tools that can read messages, and check whether
standalone Gmail or Slack credentials are already stored. Report what you found, including "none".

Then ask the user what to use for each source, with one choice per source:

- **Existing assistant connection**: record it in `sources.harnessConnections`, for example
  `[{"source": "gmail", "via": "claude-gmail"}]`. `source` is the cursor key and `Message.source`;
  `via` names the host connection. No new credential is needed.
- **Standalone read-only connector**: capture its credentials under
  [out-of-band credentials](#out-of-band-credentials) and run the Gmail sign-in when needed.
- **Disabled**: leave it out; planning works without messages.

Never pick for the user and never treat silence as a choice. Harness connections are read-only for
Daily Tasks: never send, reply to, draft, label, archive, mark read or otherwise modify messages.

Tell the user the first pull for a source without a saved cursor reads **no more than 7 days** back
by default (`sources.initialLookbackDays: 7`). Let them accept 7 or give another whole number of days;
reject zero, negative or non-integer values, explain the valid range and ask again. Save the accepted
value in the project `profile.json` (`daily-tasks-mcp` reads `sources.initialLookbackDays`, then
top-level `initialLookbackDays`; `--initial-lookback-days` overrides both). The window applies only to
first pulls: once a source's cursor is saved in `<stateRoot>/fetch-cursors.json`, every later pull
starts from that cursor, for harness connections and standalone connectors alike. On re-entry, reuse
saved choices and change them only when the user asks.

### Out-of-band credentials

Never ask the user to paste a secret (vault token, OAuth client secret, Slack token, API key) into
chat, and never put one in tool arguments, Markdown, JSON profiles or shell commands. If the user
pastes one anyway, do not repeat it; tell them to rotate it and capture the new value out of band.

- From the agent: call `daily_tasks_capture_secret` with `namespace` and `key` (optional
  `prompt_message`, `provider`). Tell the user a local browser page opens (its `127.0.0.1` URL is also
  on the server's stderr) and wait; the reply carries only the receipt (`namespace`, `key`,
  `provider`, `stored_at`). Report that receipt. On timeout or cancellation, offer to retry.
- From a terminal: ask the user to run `uv run python -m daily_tasks.auth.secret` themselves, for
  example `... gmail`, `... slack` or `... capture NAMESPACE KEY`; it prompts with masked input.

Credentials to capture during setup, only when the user wants that connector or vault:

- Gmail OAuth client: `communication/gmail-client-id` and `communication/gmail-client-secret`
  (`daily_tasks.auth.secret gmail`, add `--no-client-secret` for clients without one).
- Slack token: `communication/slack` (`daily_tasks.auth.secret slack`).
- Cloud key vault: the user runs `uv run python -m daily_tasks.auth.secret vault --name NAME --kind KIND`
  (Bitwarden Secrets Manager: `--kind bitwarden-secrets`, plus `--project-id`). It seals the vault's
  access token locally and registers the vault, after which `provider: NAME` stores secrets there. Only
  kinds of a registered `CloudKeyVaultFactory` are accepted; `--help` lists them.

Storage providers are `aesLocal` (encrypted locally, the default), `literal` (unencrypted, only for
non-secret values) and each configured vault. Environment variables (`GMAIL_CLIENT_ID`,
`GMAIL_CLIENT_SECRET`, `SLACK_BOT_TOKEN`) still take precedence over stored values.

First-run Gmail sign-in is interactive and read-only (`gmail.readonly`): after the client id (and
secret, when the OAuth client has one) is stored or set in the environment, the user runs
`uv run python -m daily_tasks.auth.gmail --config-dir <userHome>/.nyssa-ai/daily-tasks`
(or with `python -m daily_tasks.auth.gmail`).
The grant is sealed in the keyring-backed configuration store; never ask for, print or
write tokens or client secrets to Markdown, JSON profiles or chat. Gmail and Slack
connectors are optional; a failing connector is reported on the screen and does not
block planning.
