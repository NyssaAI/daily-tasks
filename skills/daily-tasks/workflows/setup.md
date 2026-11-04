> [!IMPORTANT] Scope Directive
> This workflow owns initial setup and explicit updates to Daily Tasks identity, timezone, priorities, storage bindings, MCP server registration, communication connectors, and out-of-band secret capture. It does NOT own candidate extraction (`capture.md`), record creation or repair (`records.md`), daily planning (`plan.md`), check-in reconciliation (`checkin.md`), or low-level tool/template schemas (owned by `../references/cli.md` and `../references/templates.md`).

# Set up Daily Tasks

Run this workflow on first use, whenever project setup is not already done (missing workspace `profile.json` or unresolved `projectsRoot`, `dailyPlansRelative`, `user.email`, or `timezone`), or when the user explicitly requests a configuration change. Reference [MCP / CLI interface](../references/cli.md) for server/auth parameters and [record conventions](../references/records.md) for output root rules.

## 1. Pre-flight and scope selection

1. **Keep the user informed**: Announce each setup phase clearly (checking profiles, detecting `uv`/`python`, registering the MCP server, configuring connectors, and placing templates). Never run silent multi-command probe loops.
2. **Bind immutable roots**:
   - Use the host's established absolute `workspaceRoot` (or captured initial workspace binding) and verified `homeRoot`.
   - Never infer a project root from the plugin installation directory or a later subprocess `cwd`.
   - Pass only absolute paths to tools and scripts.
3. **Read existing profile layers**:
   - Inspect `<userHome>/.nyssa-ai/daily-tasks/profile.json` and `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` (or accepted custom pointers in `configurationSources`) directly without recursively scanning home directories.
   - If a selected `profile.json` contains malformed JSON, stop and report the parse error without overwriting the file or falling back to defaults.
   - Preserve `configurationSources: {schemaVersion: 1, user: {profilePath: ABSOLUTE_PATH_OR_NULL}, project: {profilePath: ABSOLUTE_PATH_OR_NULL}}`, `workspaceRoot`, `homeRoot`, and `stateRoot` unchanged across turns.
4. **Select target write scope**:
   - Apply precedence: explicit current-request overrides (`preferenceOverrides`, never persisted) > project `profile.json` > user `profile.json`.
   - Use **user scope** (`<userHome>/.nyssa-ai/daily-tasks/profile.json`) when the user explicitly requests a personal/all-projects setting or when no workspace is established (personal-only setup).
   - Use **project scope** (`<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`) when a workspace is established and the user is configuring workspace setup or project preferences.
   - Do not ask routine scope questions when these rules determine the target scope.
   - When `sharedScopes` aliases user and project profiles to the same file, warn the user that shared preference changes affect all sessions using that file, validate the full v2 document, and merge only the requested scope's changed leaves.

## 2. Identity, timezone, and workspace storage

1. **Resolve identity, timezone, and priorities**:
   - Reuse known `user.name` and `user.email`; ask only when missing.
   - Default `timezone` to `"system"` and `priorities` to `[]` without asking routine questions, unless an explicit IANA timezone or priority list was supplied.
   - Resolve and report the actual host IANA timezone when persisting `"system"`; if host timezone detection fails, ask the user for an explicit IANA timezone (never silently fall back to `UTC`).
   - Update `priorities` only on an explicit user request, preserving the user's stated reason.
2. **Establish workspace output bindings** *(skip for personal-only setup)*:
   - Reuse existing accepted `workspaceRoot`, `projectsRoot`, and `dailyPlansRelative` bindings when present.
   - If no workspace is established and the request needs projects or a daily plan, ask the user which directory to bind as `workspaceRoot`.
   - If `projectsRoot` or `dailyPlansRelative` is unresolved, ask for the missing location(s) in a single prompt, offering `projects/` and `daily-plans/` (or `2-areas/daily-plans` for PARA vaults) under the bound workspace.
   - Reject any relative directory containing path traversal (`..`) outside its accepted root.
   - Ensure `dailyPlansRelative` stays inside `workspaceRoot` (`projectsRoot` may point to an explicitly chosen external collection) and never points inside `.nyssa-ai/` configuration or operating state.
3. **Write Schema Version 2 profile**:
   - Persist only the selected scope's fields using Schema Version 2:
     ```json
     {
       "schema_version": 2,
       "user": {"name": "Example User", "email": "user@example.com"},
       "timezone": "America/Chicago",
       "priorities": []
     }
     ```
   - Include project bindings (`workspaceRoot`, `projectsRoot`, `dailyPlansRelative`, `sources`, `templates`) only in project-scope profiles.
   - Never persist credentials, message bodies, or cache paths in `profile.json`.
   - Do not append a project decision-log entry for personal-scope setup or updates.
4. **Place visible workspace templates** *(skip for personal-only setup)*:
   - Follow [custom templates](../references/templates.md) and [template updates](../references/template-updates.md) to place missing active templates (`projectIndex`, `dailyPlan`, `milestone`, `task`, `planDayReview`) in the workspace's templates directory and record initial baselines in `templates/updates.json`.
   - Preserve existing custom template files, pointers, and `null` resets without reformatting existing records.
   - Provide clickable links to the workspace templates directory and registered template files in the setup summary.

## 3. MCP server registration

1. **Detect Python runtime**:
   - Run a single lookup (`where.exe uv` on Windows or `which uv` on POSIX). **Never** recursively scan the filesystem for `uv.exe`.
   - If `uv` is available: configure the server command with `uv run --directory <pluginRoot> daily-tasks-mcp`.
   - If `uv` is missing: inform the user that `uv` is recommended (`powershell -c "irm https://astral.sh/uv/install.ps1 | iex"` on Windows or `curl -LsSf https://astral.sh/uv/install.sh | sh` on POSIX) and fall back to host `python` (>=3.12) with `PYTHONPATH=<pluginRoot>/src` and `python -m daily_tasks.server`.
2. **Register the MCP server in the host**:
   - With `uv`: `agy mcp add daily-tasks uv run --directory <pluginRoot> daily-tasks-mcp`
   - With host Python: `agy mcp add --env "PYTHONPATH=<pluginRoot>/src" --env "DAILY_TASKS_LOG_LEVEL=Debug" daily-tasks python -m daily_tasks.server`
   - Confirm MCP registration and `daily_tasks_*` tool availability to the user. Never invoke `daily-tasks-mcp` directly as a CLI subprocess.

## 4. Communication sources and initial lookback

1. **Step 1 (Inventory & Present)**:
   - Inspect which Email (Gmail, Outlook) and Chat (Slack, Teams) integrations or MCP servers the host already provides (Claude, Codex, Antigravity, Cursor), and check whether standalone Gmail or Slack credentials are already stored in the local profile or secrets vault.
   - **MUST** output a clear Markdown table or bulleted summary to the user displaying the detected connections across Email (Gmail, Outlook) and Chat (Slack, Teams) **before** prompting for choices:

     | Channel / Source | Discovered Host Connections / MCP Servers | Stored Standalone Credentials |
     | :--- | :--- | :--- |
     | **Email** (Gmail, Outlook) | `<e.g. Composio, native host tools, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |
     | **Chat** (Slack, Teams) | `<e.g. Composio, native host tools, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |

   - **Do not call interactive question tools (e.g. `ask_question`) without first rendering the discovered connection inventory to the user.**
2. **Step 2 (Dynamic Prompting)** *(never choose silently or treat silence as a choice)*:
   - Formulate the per-source selection options dynamically based strictly on the inventory rendered in Step 1:
     - **Existing assistant connection (`<discovered-integration-name>`)**: Offer this option **only** if a host MCP server or harness integration was actually detected in Step 1 (e.g., `Existing assistant connection (Composio)` or `Existing assistant connection (claude-gmail)`). **Never** presume or hardcode `"Composio"` if Composio is not registered in the host's MCP configuration. When selected, record `{"source": "<name>", "via": "<discovered-integration-name>"}` in `sources.harnessConnections` (strictly read-only; never send, reply, draft, label, archive, or mark read).
     - **Standalone read-only connector**: Always offer this option, explicitly noting whether standalone credentials are already saved or whether credential setup is needed via [Out-of-band credentials](#out-of-band-credentials) and Gmail OAuth sign-in.
     - **Disabled**: Always offer this option; when selected, omit the source so planning operates without message ingestion.
3. **Step 3 (Configure initial lookback window)**:
   - Inform the user that a source's first pull without a saved cursor reads back **7 days** by default (`sources.initialLookbackDays: 7`).
   - Accept `7` or another positive integer supplied by the user; reject zero, negative, or non-integer values and ask again.
   - Persist `sources.initialLookbackDays` in the project `profile.json` (subsequent pulls automatically resume from `<stateRoot>/fetch-cursors.json`).

### Out-of-band credentials

Enforce strict secret hygiene whenever standalone connectors or cloud vaults are configured:
- **Never** ask the user to paste a secret (OAuth client secret, Slack token, vault token, API key) into chat, and **never** pass a secret in tool arguments, Markdown, JSON profiles, or shell command lines.
- If the user pastes a secret into chat, do not echo it; instruct them to rotate the credential and capture the replacement out of band.
- Capture required secrets using one of two sanctioned paths:
  1. **Via MCP tool**: Call `daily_tasks_capture_secret(namespace, key, prompt_message?, provider?)`, inform the user that a local `127.0.0.1` loopback browser page has opened, and report the returned receipt (`namespace`, `key`, `provider`, `stored_at`).
  2. **Via user terminal**: Ask the user to run `uv run python -m daily_tasks.auth.secret` directly in their terminal:
     - Gmail OAuth client (`communication/gmail-client-id` and `communication/gmail-client-secret`): `uv run python -m daily_tasks.auth.secret gmail` (add `--no-client-secret` for public clients).
     - Slack token (`communication/slack`): `uv run python -m daily_tasks.auth.secret slack`.
     - Cloud key vault (`bitwarden-secrets` / `bws` / `bitwarden`): `uv run python -m daily_tasks.auth.secret vault --name NAME --kind bitwarden-secrets --project-id ID`.
- For first-run interactive Gmail OAuth (`gmail.readonly`), ask the user to run `uv run python -m daily_tasks.auth.gmail --config-dir <userHome>/.nyssa-ai/daily-tasks` after storing the Gmail client credentials.

## Verification

Before reporting setup completion or continuing to a downstream workflow:
- [ ] Confirm the target `profile.json` exists on disk, uses `schema_version: 2`, and contains no credentials or invalid traversal paths.
- [ ] Confirm personal-only setup created no workspace bindings, workspace templates, project records, or project decision-log entries.
- [ ] Confirm workspace setup resolved distinct configuration, operating-state (`.nyssa-ai/daily-tasks`), `projectsRoot`, and `dailyPlansRelative` locations, and placed/linked visible workspace templates.
- [ ] Confirm the discovered Email/Chat connection inventory was rendered to the user before prompting for connector choices, and only detected host integrations were offered as `Existing assistant connection (<discovered-integration-name>)`.
- [ ] Report the saved profile path(s), resolved IANA timezone, and registered MCP/connector status to the user, then continue the original request if setup was triggered as a prerequisite.
