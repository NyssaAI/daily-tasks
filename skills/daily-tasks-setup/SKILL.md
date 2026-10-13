---
name: daily-tasks-setup
description: Set up or explicitly update Daily Tasks identity, timezone, priorities and storage locations. Use on first use or when the user changes personal planning preferences.
---

# Set up Daily Tasks

Resolve configuration before asking questions. Load the
[CLI](../daily-tasks/references/cli.md) for context/profile/log operations and
[record conventions](../daily-tasks/references/records.md) for output bindings.
Use the host's established absolute vault root or captured initial vault workspace
binding and verified user home. A nested directory, plugin installation or later
subprocess cwd cannot establish another project. Installation scope never determines
preference scope. Paths passed to scripts are absolute.

## Read and select a write scope

Read both applicable levels: `<userHome>/.nyssa-ai/daily-tasks/profile.json` and
`<vaultRoot>/.nyssa-ai/daily-tasks/profile.json`. Within each level reuse an explicit
accepted pointer; otherwise prefer canonical `.nyssa-ai`, then `.nyssaai`, then
`.nyssa`. These legacy locations remain supported without relocation or deletion.
Never merge duplicate locations in one scope; report shadowed locations. Read exact
paths without recursively scanning home. Diagnose malformed selected profiles.

`resolve-context` returns `configurationSources: {schemaVersion: 1, user:
{profilePath: ABSOLUTE_PATH_OR_NULL}, project: {profilePath: ABSOLUTE_PATH_OR_NULL}}`.
Null records deliberate absence. Preserve this descriptor unchanged, together with
vaultRoot, homeRoot and stateRoot, for preparation, save, maintenance and recovery.
Revalidate those roots on continuation. New layered flows pass the descriptor;
legacy `profilePath` or `configRoot` selects one exclusive profile. Never pass legacy
selectors alongside the descriptor. The returned configRoot can identify a write
destination but cannot represent the complete layered read context.

Explicit current-task choices override project preferences, which override user
preferences. Pass supported one-off leaves in optional `preferenceOverrides` (without
schema_version); preserve them through that request's continuation and never save them.
The resolver reports winning preferenceSources and scoped writableScopes.
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
even in a project session. Otherwise new setup uses project scope when a vault is
established, and user scope when no project is established. Do not ask routine scope
questions when these rules resolve the destination. A project write needs a resolved
project; personal preference setup needs no vault or project collection.

Ask only for missing name and email; reuse trusted supplied identity. Default timezone
to `system` and priorities to an empty list without routine questions. Resolve and
report the actual host timezone while persisting `system`; preserve an explicit IANA
zone unless changed. Failed host detection requires an explicit IANA zone, never a
silent UTC fallback. Accepted priorities change only on an explicit request, retaining
the user's reason. Do not fabricate work to complete setup.

## Stored preferences and project bindings

### Establish storage when no PARA vault exists

`vaultRoot` means the bound workspace folder; it does not require Obsidian or a
PARA layout. An ordinary folder is supported. Personal-only setup uses the verified
user home, leaves project configuration absent and asks no workspace/storage question.

When the requested work needs project records or a daily plan, reuse accepted
workspace and output locations first. If no workspace is established, ask where the
user wants to keep that work; their chosen folder establishes the absolute vaultRoot.
Do not use the plugin installation or an incidental current directory as that choice.
In a recognized PARA workspace, reuse its actual Projects and Areas directory names
for missing output bindings. In an ordinary workspace, ask only for unresolved
project-record and daily-plan locations, together when both are missing; offer
`projects/` and `daily-plans/` under the chosen workspace as concrete choices.
Persist the selected projectsRoot and dailyPlansRelative in the project layer and
continue the original request. Explain that daily plans belong inside the workspace;
an explicitly assigned projects collection may be outside it. Preserve existing
bindings, including the packaged daily-plan default when already accepted.

Do not require a PARA conversion or create Projects/Areas/Resources/Archives folders
to complete ordinary-folder setup. Bundled templates remain usable; user-supplied
templates follow the non-PARA storage rules in [custom templates](../daily-tasks/references/templates.md).
Configuration and operating-state locations remain conventional; ask about the
user's work storage, not internal profile/cache/state paths.

New profiles use schema version 2 and may contain only the selected scope's values:

```json
{
  "schema_version": 2,
  "user": {"name": "Example User", "email": "user@example.com"},
  "timezone": "system",
  "priorities": []
}
```

For a project layer, add accepted project bindings, for example `vaultRoot: "."`,
`projectsRoot: "./1-projects"`, and `dailyPlansRelative: "2-areas/daily-plans"`.
These are project-only bindings, never reusable user defaults. Resolve projectsRoot
from an existing accepted collection; ask only if ambiguous. The default daily-plan
output is `2-areas/daily-plans`. Existing full version-1 profiles remain supported;
a home version-1 absolute vault binding remains limited to that vault, while `.`
uses the explicitly bound vault.

Supported preferences are partial `user.name`/`user.email`, timezone, priorities,
`templates.projectIndex`, `templates.dailyPlan`, `templates.milestone`,
`templates.task`, `templates.planDayReview`, and `projectIndex.ttlSeconds`.
Scalars and arrays replace (including an empty priority list); supported object
leaves merge. Omission inherits. Version 2 permits null only at timezone, priorities,
each template kind and projectIndex.ttlSeconds to select packaged defaults (`system`,
empty priorities, bundled formatting, 14400 seconds), masking lower layers. Removing
that scoped key restores inheritance. Null identity, bindings and whole object
containers are invalid. Version 1 keeps its original null validation contract.
Paths use existing absolute paths, `~/` for home, or `./` relative to the bound vault;
resolve paths before passing them to consumers. Read custom template guidance only
when the user supplies or changes formatting.

For template update choices and lasting ask/latest/keep policies, follow
[template updates](../daily-tasks/references/template-updates.md). Use the selected
scope's `template-state` operation; do not add unsupported policy fields to profile.json.
Retained snapshots/choices live beside that profile under `templates/updates.json`.
They are configuration assets, not vault operating state. Registration and template
adoption never authorize reformatting existing documents.

Validate the stored layer with `validate-profile` before writing through normal file
tools. Validate the effective task context separately before continuing vault work.
Missing project bindings do not prevent personal setup. Do not persist credentials,
private message copies or cache paths. Keep configuration outside installed source.
Check Node >=22 and CLI --help before invoking scripts.

After vault configuration resolves, follow
[visible template placement](../daily-tasks/references/templates.md#visible-templates-in-a-para-vault)
for all five template kinds. In an established PARA vault, place missing active
templates in its actual Resources/templates directory and register the paths.
Skills own those Markdown/profile writes; the CLI proposes placement and records
baselines. Preserve existing pointers, null resets and destination files. Link the
directory and registered files in setup results so the user can inspect/edit them.
Personal-only setup needs no vault templates. Installation itself never selects a vault.

## Operating state and output

Configuration contains profile.json and optional templates. State contains vault-local
pending operations, completed rollover/removal history, candidates, review progress
and reconciliation baselines. Daily Markdown plans and project records belong to their
resolved output roots, never below either configuration root or state storage.

State discovery examines authoritative contents separately from preferences and
caches. A canonical profile-only directory cannot hide legacy completed state.
Reuse a verified established state binding; otherwise use the sole authoritative
store. Divergent stores require explicit reconciliation even without pending work;
an empty explicit target beside populated history is also an error. Use the reported
established path or resolve the conflict explicitly; never silently redirect a session.
Identical copies may use established binding or canonical precedence. Never combine
stores or select by modification time. Create canonical state only when none exists.
A preference-scope change never authorizes moving state or outputs.

Report changed settings and their path. **Personal setup and updates complete without
a vault decision-log entry**, even in a project session; never replay them into a
later vault log or create a separate audit system. Project preference changes retain
the log CLI behavior with empty record_ids. Report resolved timezone and separate
configuration/state/output roots when applicable. Create state only when needed.
Setup authorizes no work creation, ownership changes or schema migration. When reached
from another request, continue that already-authorized work after resolving its scope.

## Optional OpenClaw prewarm

After project setup succeeds, an OpenClaw host with the separate
`daily-tasks-openclaw` native adapter may offer project-index prewarming. Register it
only when the user accepts the optional automation; setup of ordinary preferences does
not imply consent. Default to one hour and use the user's explicit interval when given:

```text
openclaw daily-tasks setup-prewarm --vault-root ABSOLUTE_VAULT --home-root ABSOLUTE_HOME [--profile-path ABSOLUTE_PROFILE | --configuration-sources JSON] [--state-root ABSOLUTE_STATE] [--every 1h]
```

Run `--dry-run` first when inspecting the declaration. The adapter reconciles by a
scope-derived declaration key, uses exact command argv, starts no agent or model, and
delivers no chat output. Verify the returned automation and its command payload.
Re-running with another `--every` value updates the declaration; routine reconciliation
preserves an operator-disabled job unless `--disabled` is explicitly supplied.
For layered settings pass the returned `configurationSources` as one exact JSON argv
value and the established `stateRoot`. Preserve explicit null source absences. Do not
serialize effective preferences, one-off overrides, dates or clocks into the job.
Legacy profile selectors remain exclusive. Changing source bindings creates a different
declaration, not an update to the old job. When replacing a known job, show both scopes
and obtain the user's explicit replacement choice; use OpenClaw's supported
[disable/remove controls](https://docs.openclaw.ai/automation/cron-jobs/managing-jobs)
for that job before registering its replacement. The adapter does not discover, delete
or migrate other declarations. Reuse any replacement choice already supplied.
Other hosts continue with on-demand behavior and need no adapter. Failure, disablement
or removal of the automation never changes correctness: every inventory consumer still
performs the TTL, local-date, scope, source-membership and metadata checks itself.
