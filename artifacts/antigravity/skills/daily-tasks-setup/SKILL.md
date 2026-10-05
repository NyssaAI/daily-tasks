---
name: daily-tasks-setup
description: Set up or explicitly update Daily Tasks identity, timezone, priorities and storage locations. Use on first use or when the user changes personal planning preferences.
---

# Set up Daily Tasks

Read [record conventions](../daily-tasks/references/records.md) and
[CLI](../daily-tasks/references/cli.md). Collect user name/email, IANA timezone,
stated priorities, and explicit absolute configRoot, vaultRoot and projectsRoot.
Ask only for missing values. Config root must be the user-selected `.nyssaai/daily-tasks/`
directory (for example below home or the vault); do not assume which. Confirm the
resolved paths in the setup summary. Respect existing files and use local PARA/file
guidance only if installed/applicable, with explicit user instructions taking precedence.

Treat configuration and operating state separately from user output:

| Location | Contents |
| --- | --- |
| `configRoot` | `profile.json`, reconciliation baselines, pending operations, candidates and check-in progress |
| `<vaultRoot>/<dailyPlansRelative>` | User-facing daily Markdown plans |
| `projectsRoot` | Project, milestone, task, blocker and definition-of-done documents |

Save the profile at `<configRoot>/profile.json`. Resolve the daily-plan output directory
from `vaultRoot` and `dailyPlansRelative`; never use configRoot as an output default or
fallback. Do not place daily plans or accepted task documents in `.nyssaai/daily-tasks/`.
If output settings are missing or resolve into the configuration/state directory, ask
for the intended output location before writing. Setup's summary must show the resolved
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
