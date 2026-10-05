---
name: daily-tasks-setup
description: Set up or explicitly update Daily Tasks identity, timezone, priorities and storage locations. Use on first use or when the user changes personal planning preferences.
---

# Set up Daily Tasks

Read [record conventions](../daily-tasks/references/records.md) and
[CLI](../daily-tasks/references/cli.md). Resolve configuration before asking setup questions.
An absolute path is required for file operations; it need not be typed by the user.

## Resolve configuration and scope

1. Reuse the applicable explicit configRoot or settings pointer from the current
   request, session, project instructions or verified host binding. Honor an existing
   configured legacy location; the new convention does not authorize migration.
2. Otherwise use `<common-state-root>/daily-tasks` when an applicable `.nyssaai`
   common state root is already established. Do not append `.nyssaai` a second time.
3. Otherwise, for a known authorized vault, use `<vaultRoot>/.nyssaai/daily-tasks`.
   Check that exact location for `profile.json`. If it is absent, check the exact legacy
   `<vaultRoot>/.nyssa/daily-tasks/profile.json` and reuse it if present. If neither
   exists, initialize the conventional `.nyssaai/daily-tasks` location as part of the
   requested operation. Do not ask the user to choose between home and vault storage.
4. When no vault is selected, use an established personal common state root, or the
   verified user's home `.nyssaai/daily-tasks`, to look for an existing profile.
   This lookup does not select a vault or authorize creating project output there.
   If required scope is still unknown, ask for the intended vault/project, not an
   internal state-directory preference. Do not recursively scan home directories.

Load the selected profile before collecting missing values. Use known identity,
timezone and accepted priorities from applicable user/host context. Reuse vaultRoot,
projectsRoot and dailyPlansRelative from the profile or accepted vault conventions.
A verified vault/workspace binding can establish scope; process cwd, package location
and cache paths cannot. Check that the profile matches the requested vault/project.
Do not replace malformed profiles, overwrite conflicting values or merge different
users' state. Ask only for missing information needed for the operation or conflicts
that affect it, after applying the precedence above. Missing priority preferences do
not block record creation: use an empty list until priorities are supplied.

For an authorized vault with no daily-plan setting, use `2-areas/daily-plans` unless
an accepted local convention provides another destination. Resolve projectsRoot from
the existing project collection or accepted convention; ask only if it is ambiguous.
Report the resolved locations in the result, without a separate confirmation gate.
Respect existing files and applicable PARA/file guidance; user instructions take precedence.

Treat configuration and operating state separately from user output:

| Location | Contents |
| --- | --- |
| `configRoot` | `profile.json`, reconciliation baselines, pending operations, candidates and check-in progress |
| `<vaultRoot>/<dailyPlansRelative>` | User-facing daily Markdown plans |
| `projectsRoot` | Project, milestone, task, blocker and definition-of-done documents |

Save the profile at `<configRoot>/profile.json`. Resolve the daily-plan output directory
from `vaultRoot` and `dailyPlansRelative`; never use configRoot as an output default or
fallback. Do not place daily plans or accepted task documents in `.nyssaai/daily-tasks/`.
If output settings cannot be resolved by the rules above or resolve into the
configuration/state directory, ask for the intended output location before writing.
Setup's summary must show the resolved
configuration directory, daily-plan output directory and projects directory separately.
Reuse an existing configured state location (including legacy `.nyssa/daily-tasks/`)
until the user requests migration; do not silently move existing state or output.

Check Node >=22 and CLI --help. Use `validate-profile` before saving profile.json:

```json
{
  "schema_version": 1,
  "user": {"name": "Example User", "email": "user@example.com"},
  "timezone": "America/Chicago",
  "priorities": ["Fulfill accepted commitments", "Advance the selected project"],
  "vaultRoot": "/absolute/vault",
  "projectsRoot": "/absolute/vault/1-projects",
  "dailyPlansRelative": "2-areas/daily-plans"
}
```

Paths above are illustrative; use actual explicit platform paths. Do not store
credentials, private copies of messages, or plugin-cache paths. Write validated profile
through normal file tools; log explicit setup/priority changes through log CLI using
an empty record_ids array for profile-level changes. Retain unchanged priorities until
user accepts a proposed revision, including its reason. Never infer a preference update.
Ensure directory is separate from plugin source; no account installation needed for setup.

Create reconciliation/check-in state only as needed, not imaginary tasks/projects.
Return configured locations/timezone and capability limits. Setup does not authorize
creating work, changing existing ownership, or migrating an existing vault schema.
When setup was reached during another request, continue that already-authorized work
after resolving configuration; do not end the turn with setup alone.
