---
name: daily-tasks-setup
description: Set up or explicitly update Daily Tasks identity, timezone, priorities and storage locations. Use on first use or when the user changes personal planning preferences.
---

# Set up Daily Tasks

Resolve configuration before asking setup questions. Load the
[CLI](../daily-tasks/references/cli.md) when invoking context/profile/log operations;
load [record conventions](../daily-tasks/references/records.md) when validating
output roots or continuing into record work. This skill owns configuration discovery
and first-use questions; direct child workflows use the same procedure.
An absolute path is required for file operations; it need not be typed by the user.
Use `resolve-context` with the host's captured initial vault-root workspace binding,
or an already known absolute vaultRoot. Reuse its result for the request. It accepts
explicit profilePath/configRoot/stateRoot for established settings and legacy state.
Profile paths may use ./ (that vault), ~/ (that user's home), or existing absolute
paths. Scripts receive resolved absolute paths, independent of subprocess cwd.

## Resolve configuration and scope

1. Reuse the applicable explicit configRoot or settings pointer from the current
   request, session, project instructions or verified host binding. Honor an existing
   configured legacy location; the new convention does not authorize migration.
2. Otherwise use `<common-state-root>/daily-tasks` when an applicable `.nyssaai`
   common state root is already established. Do not append `.nyssaai` a second time.
3. Otherwise, for a known authorized vault, check `<vaultRoot>/.nyssaai/daily-tasks`.
   Check that exact location for `profile.json`. If it is absent, check the exact legacy
   `<vaultRoot>/.nyssa/daily-tasks/profile.json` and reuse it if present. If neither
   exists, continue discovery at the user's home before initializing configuration.
4. When no vault is selected, use an established personal common state root, or the
   verified user's home `.nyssaai/daily-tasks`, to look for an existing profile.
   This lookup does not select a vault or authorize creating project output there.
   If required scope is still unknown, ask for the intended vault/project, not an
   internal state-directory preference. Do not recursively scan home directories.

When no applicable profile or accepted configuration scope exists, ask once:
**"Configure Daily Tasks for this vault only, or for all vaults you access?"**

- **This vault only:** Use `<vaultRoot>/.nyssaai/daily-tasks/profile.json`.
- **All vaults I access:** Use `<userHome>/.nyssaai/daily-tasks/profile.json` for
  personal preferences. Explain that this means vaults accessed by this user;
  availability on other hosts requires replicating those preferences too.

The question is about preference scope, not internal directory selection. Resolve
the conventional location from the answer without asking the user to type or
approve paths. Explicit scope in the request already answers this question.
Reuse an existing setup without asking again; changing its scope is an explicit
configuration change, not permission to move existing state. Cross-vault preference
reuse must not reuse another vault's output roots or operating state.

First-use setup has only two routine questions:

1. The configuration scope question above, unless already answered.
2. **"What name and email should identify you as the task owner?"** Ask only for
   missing values; reuse trusted identity already supplied by the user or host.

For a new profile default `timezone` to `"system"`. Do not routinely ask for a
timezone or priorities. Use an empty priority list until the user supplies one.
`validate-profile` returns `resolvedTimezone`; report that actual zone in the setup
summary, for example **"Timezone: America/Chicago (detected from this host)."**
Persist `"system"`, not its detected value, so each host resolves its own zone.
Preserve an existing explicit IANA timezone unless the user requests a change.
If host detection fails, explain the failure and ask for an explicit IANA zone as
an exception. Do not silently fall back to UTC. Concrete conflicts or missing
required output scope may still require focused clarification.

Load the selected profile before collecting missing values; reuse accepted settings
and output roots from that profile or applicable user/host vault conventions.
A verified vault/workspace binding or the captured initial cwd of a vault-root
workspace can establish scope. A later process cwd, package location and cache paths
cannot. Check that the profile matches the requested vault/project.
Do not replace malformed profiles, overwrite conflicting values or merge different
users' state. Ask only for missing information needed for the operation or conflicts
that affect it, after applying the precedence above. Missing priorities do not block
record creation.

For an authorized vault with no daily-plan setting, use `2-areas/daily-plans` unless
an accepted local convention provides another destination. Resolve projectsRoot from
the existing project collection or accepted convention; ask only if it is ambiguous.
Report the resolved locations in the result, without a separate confirmation gate.
Respect existing files and applicable PARA/file guidance; user instructions take precedence.

Treat configuration and operating state separately from user output:

| Location | Contents |
| --- | --- |
| `configRoot` | Selected `profile.json` and optionally copied templates |
| `stateRoot` | Vault-specific baselines, pending operations, candidates and check-in progress |
| `<vaultRoot>/<dailyPlansRelative>` | User-facing daily Markdown plans |
| `projectsRoot` | Project and milestone workspaces, task/blocker records, flat input/output holding folders and legacy DoD documents |

Save the profile at `<configRoot>/profile.json`. Resolve the daily-plan output directory
from `vaultRoot` and `dailyPlansRelative`; never use configRoot as an output default or
fallback. Do not place daily plans or accepted task documents in `.nyssaai/daily-tasks/`.
If output settings cannot be resolved by the rules above or resolve into the
configuration/state directory, ask for the intended output location before writing.
Setup's summary must show the resolved
configuration directory, daily-plan output directory and projects directory separately.
The discovery precedence above also governs existing state (including legacy
`.nyssa/daily-tasks/`); scope changes never silently migrate state or output.

Check Node >=22 and CLI --help. Use `validate-profile` before saving profile.json:

```json
{
  "schema_version": 1,
  "user": {"name": "Example User", "email": "user@example.com"},
  "timezone": "system",
  "priorities": [],
  "vaultRoot": ".",
  "projectsRoot": "./1-projects",
  "dailyPlansRelative": "2-areas/daily-plans",
  "projectIndex": {"ttlSeconds": 14400}
}
```

Paths above are portable vault conventions; use the accepted actual collection.
The runtime resolver expands them for this host. Do not store
credentials, private copies of messages, or plugin-cache paths. Write validated profile
through normal file tools; log explicit setup/priority changes through log CLI using
an empty record_ids array for profile-level changes. Retain unchanged priorities until
user accepts a proposed revision, including its reason. Never infer a preference update.
Ensure directory is separate from plugin source; no account installation needed for setup.

Create reconciliation/check-in state only as needed, not imaginary tasks/projects.
When the user supplies an example/template or explicitly changes formatting, load
[custom templates](../daily-tasks/references/templates.md) for registration, portable
profile fields, precedence and adaptation. Template preferences are optional; do not
add template questions to routine setup. Registration does not authorize rewriting
existing records.
Return configured locations/timezone and capability limits. Setup does not authorize
creating work, changing existing ownership, or migrating an existing vault schema.
When setup was reached during another request, continue that already-authorized work
after resolving configuration; do not end the turn with setup alone.
