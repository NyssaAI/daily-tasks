> [!IMPORTANT] Scope Directive
> This workflow owns harness-aware initial setup, legacy v1 migration, and explicit updates to Daily Tasks identity, timezone, priorities, storage bindings, MCP server registration, communication connectors, and out-of-band secret capture. It does NOT own candidate extraction (`capture.md`), record creation or repair (`records.md`), daily planning (`plan.md`), check-in reconciliation (`checkin.md`), or low-level tool/template schemas (owned by `../references/cli.md`, `../references/harness-setup.md`, and `../references/templates.md`).

# Set up Daily Tasks

Run this workflow on first use, whenever **any** mandatory setup gate is incomplete (missing or unreachable `daily_tasks_*` MCP tools, missing or non-v2 `profile.json`, unmigrated legacy `.nyssaai/daily-tasks/profile.json`, unresolved `projectsRoot` / `dailyPlansRelative` / `user.email` / IANA `timezone`, missing workspace templates baseline, or unconfigured `sources`), or when the user explicitly requests a configuration change. Reference [harness setup](../references/harness-setup.md) for per-harness registration/discovery, [MCP / CLI interface](../references/cli.md) for server/auth parameters, and [record conventions](../references/records.md) for output root rules.

## 1. Pre-flight, harness detection, and scope selection

1. **Keep the user informed**: Announce each setup phase clearly (detecting the active harness, checking profiles, registering/verifying the MCP server, configuring connectors, and placing templates). Never run silent multi-command probe loops.
2. **Identify the active harness and plugin root**:
   - Detect the current harness (`OpenClaw`, `Google Antigravity`, `Claude Code`, `Claude Cowork`, `Codex`, `Cursor / Grok Bot`, or `Hermes Agent`) from the live tool surface and environment per [harness setup](../references/harness-setup.md#harness-identification). Never assume `agy` or another harness's CLI without checking.
   - Resolve `<pluginRoot>` from the actual installed Daily Tasks plugin directory on the host.
3. **Bind immutable roots**:
   - Use the host's established absolute `workspaceRoot` (or captured initial workspace binding) and verified `homeRoot`.
   - Never infer a project root from `<pluginRoot>` or a later subprocess `cwd` (for example, in OpenClaw the agent scratch workspace `/var/lib/.../workspace` is distinct from the user's vault under `/srv/vaults/...`).
   - Pass only absolute paths to tools and registration commands.
4. **Read existing v2 profiles and detect legacy v1 profiles**:
   - Inspect `<userHome>/.nyssa-ai/daily-tasks/profile.json` and `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json` (or accepted custom pointers in `configurationSources`) directly without recursively scanning home directories.
   - If a canonical `.nyssa-ai/daily-tasks/profile.json` is absent, check whether a legacy `<userHome>/.nyssaai/daily-tasks/profile.json` or `<workspaceRoot>/.nyssaai/daily-tasks/profile.json` exists:
     - When a legacy v1 profile is found, present its discovered `user`, `timezone`, `priorities`, `projectsRoot`, and `dailyPlansRelative` values to the user and offer to migrate them into canonical Schema Version 2 `.nyssa-ai/daily-tasks/profile.json` (leaving the legacy `.nyssaai` file untouched unless separate removal is authorized).
   - If any inspected `profile.json` contains malformed JSON, stop and report the exact parse error and path without overwriting the file or falling back to defaults.
   - Preserve `configurationSources: {schemaVersion: 1, user: {profilePath: ABSOLUTE_PATH_OR_NULL}, project: {profilePath: ABSOLUTE_PATH_OR_NULL}}`, `workspaceRoot`, `homeRoot`, and `stateRoot` unchanged across turns.
5. **Select target write scope**:
   - Apply precedence: explicit current-request overrides (`preferenceOverrides`, never persisted) > project `profile.json` > user `profile.json`.
   - Use **user scope** (`<userHome>/.nyssa-ai/daily-tasks/profile.json`) when the user explicitly requests a personal/all-projects setting or when no workspace is established (personal-only setup).
   - Use **project scope** (`<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`) when a workspace is established and the user is configuring workspace setup or project preferences.
   - Do not ask routine scope questions when these rules determine the target scope.
   - When `sharedScopes` aliases user and project profiles to the same file, warn the user that shared preference changes affect all sessions using that file, validate the full v2 document, and merge only the requested scope's changed leaves.

## 2. Identity, timezone, and workspace storage

1. **Resolve identity, timezone, and priorities**:
   - Reuse known `user.name` and `user.email` (including confirmed legacy v1 values); ask only when missing.
   - Default `timezone` to `"system"` and `priorities` to `[]` without asking routine questions, unless an explicit IANA timezone or priority list was supplied.
   - Resolve and persist the actual host IANA timezone (e.g. `"America/Chicago"`, never literal `"system"`) when `"system"` is selected; if host timezone detection fails, ask the user for an explicit IANA timezone and never silently fall back to `UTC`.
   - Update `priorities` only on an explicit user request, preserving the user's stated reason.
2. **Establish workspace output bindings** *(skip for personal-only setup)*:
   - Reuse existing accepted `workspaceRoot`, `projectsRoot`, and `dailyPlansRelative` bindings when present.
   - If no workspace is established (or the current `cwd` is an agent runtime home rather than the user's vault/project directory) and the request needs projects or a daily plan, ask the user which absolute directory to bind as `workspaceRoot`.
   - If `projectsRoot` or `dailyPlansRelative` is unresolved, ask for the missing location(s) in a single prompt, offering `projects/` and `daily-plans/` (or `1-projects` and `2-areas/daily-plans` when a PARA vault layout is detected under `workspaceRoot`).
   - Reject any relative directory containing path traversal (`..`).
   - Ensure `dailyPlansRelative` stays inside `workspaceRoot` (`projectsRoot` may point to an explicitly chosen absolute external collection) and never points inside `.nyssa-ai/` configuration or operating state.
3. **Write Schema Version 2 profile**:
   - For **personal-only setup**, persist strictly the personal v2 fields to `<userHome>/.nyssa-ai/daily-tasks/profile.json` and create no workspace directories, templates, or project files:
     ```json
     {
       "schema_version": 2,
       "user": {"name": "Example User", "email": "user@example.com"},
       "timezone": "America/Chicago",
       "priorities": []
     }
     ```
   - For **project-scope setup**, persist `"schema_version": 2` along with `"workspaceRoot"`, `"projectsRoot"`, `"dailyPlansRelative"`, `"sources"`, and `"templates"` (plus `"user"`, `"timezone"`, and `"priorities"` when configured at project scope) in `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`.
   - Never persist credentials, message bodies, or cache paths in `profile.json`.
4. **Place visible workspace templates** *(skip for personal-only setup)*:
   - Follow [custom templates](../references/templates.md) and [template updates](../references/template-updates.md) to place missing active templates (`projectIndex`, `dailyPlan`, `milestone`, `task`, `planDayReview`) in the workspace's templates directory (such as `./templates/` or `./3-resources/templates/` in PARA vaults), register them under `templates` in `profile.json`, and write initial baselines in `<workspaceRoot>/.nyssa-ai/daily-tasks/templates/updates.json`.
   - Preserve existing custom template files, pointers, and `null` resets without reformatting existing records.

## 3. Harness-aware MCP server registration *(skip for personal-only setup)*

1. **Check live MCP tool availability first**:
   - Inspect whether `daily_tasks_start_session` and sibling `daily_tasks_*` MCP tools are already exposed in the current harness (for example via `catalog.search("daily_tasks")` in OpenClaw or the active MCP tool catalog in Antigravity, Claude, Codex, Cursor, or Hermes).
   - If the `daily_tasks_*` tools are already live, skip registration and verify connectivity once `profile.json` is written.
2. **Resolve the Python launcher**:
   - Run a single lookup (`where.exe uv` on Windows or `which uv` on POSIX); **never** recursively scan the filesystem.
   - Prefer `uv run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>` when `uv` is installed; otherwise verify Python `>=3.12` (`python3` / `python`) and use `PYTHONPATH=<pluginRoot>/src` with `-m daily_tasks.server --workspace-root <workspaceRoot>`.
3. **Register `daily-tasks` using the active harness's native mechanism** ([exact commands and schemas](../references/harness-setup.md#per-harness-mcp-server-registration)):
   - **OpenClaw**: Delegate `daily-tasks` stdio MCP registration and `openclaw mcp reload` through the native `openclaw` system tool (never `sudo`), or provide the operator `openclaw mcp add daily-tasks ... && openclaw mcp reload` command if delegation is restricted.
   - **Google Antigravity**: Run `agy mcp add` with `--` before command flags (`agy mcp add daily-tasks -- uv run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>`, or `agy mcp add --env "PYTHONPATH=<pluginRoot>/src" daily-tasks -- python3 -m daily_tasks.server --workspace-root <workspaceRoot>`).
   - **Claude Code / Claude Cowork**: Approve `.mcp.json` or run `claude mcp add daily-tasks -- ...` in Claude Code; in Cowork, rely on the bundled `.mcp.json` archive and instruct the user to enable local plugin MCP execution under Customize > Plugins if blocked.
   - **Codex**: Use portable `mcp.json` discovery or run `codex mcp add daily-tasks -- ...` (adding `--env PYTHONPATH=<pluginRoot>/src` for the `python3` fallback).
   - **Cursor / Grok Bot**: Use installed plugin `mcp.json` or update `<workspaceRoot>/.cursor/mcp.json`; on Grok Bot, verify MCP tool exposure and stop with exact host capability guidance if local stdio MCP is unavailable.
   - **Hermes Agent**: Enable `.hermes/plugins/daily-tasks/` (`HERMES_ENABLE_PROJECT_PLUGINS`) or register `daily-tasks` under `mcp_servers` in `~/.hermes/config.yaml`.
4. **Enforce live MCP verification**:
   - Confirm `daily_tasks_*` MCP tools are callable in the harness (e.g. `daily_tasks_get_fetch_window(workspace_root="<workspaceRoot>")` after writing `profile.json`).
   - **Never** invoke `daily-tasks-mcp` or `python -m daily_tasks.server` as a one-shot CLI subprocess, and if the harness requires starting a new turn/session for newly registered MCP tools to load, stop cleanly after finishing file setup and ask the user to continue on the next turn.

## 4. Harness-aware communication sources and initial lookback *(skip for personal-only setup)*

1. **Step 1 (Inventory & Present)**:
   - Inspect Email (`gmail`, `outlook`) and Chat (`slack`, `teams`) integrations available in the **detected harness** per [harness connector discovery](../references/harness-setup.md#harness-aware-connector-discovery) (OpenClaw `catalog.search` / read-only channels, or active MCP servers in Antigravity, Claude, Codex, Cursor, and Hermes), plus stored standalone credentials in `<userHome>/.nyssa-ai/daily-tasks`.
   - **MUST** output a clear Markdown table or bulleted summary displaying the detected connections across Email and Chat **before** prompting for choices:

     | Channel / Source | Discovered Host Connections / MCP Servers | Stored Standalone Credentials |
     | :--- | :--- | :--- |
     | **Email** (Gmail, Outlook) | `<e.g. OpenClaw/MCP integration name, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |
     | **Chat** (Slack, Teams) | `<e.g. OpenClaw/MCP integration name, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |

   - **Do not call interactive question tools (e.g. `ask_question`) without first rendering the discovered connection inventory to the user.**
2. **Step 2 (Dynamic Prompting)** *(never choose silently or treat silence as a choice)*:
   - Formulate per-source options dynamically from Step 1:
     - **Existing assistant connection (`<discovered-integration-name>`)**: Offer **only** if actually detected in Step 1 (never hardcode `"Composio"` or another connector when absent). When selected, record `{"source": "<name>", "via": "<discovered-integration-name>"}` in `sources.harnessConnections` (strictly read-only).
     - **Standalone read-only connector**: Always offer, noting whether standalone credentials are already saved or require [Out-of-band credentials](#out-of-band-credentials) and Gmail OAuth sign-in.
     - **Disabled**: Always offer; when selected, record the disabled/omitted choice so `sources` reflects that connector setup was completed.
3. **Step 3 (Configure initial lookback window)**:
   - Inform the user that a source's first pull without a saved cursor reads back **7 days** by default (`sources.initialLookbackDays: 7`).
   - Accept `7` or another positive integer supplied by the user; reject zero, negative, or non-integer values and ask again.
   - Persist `sources` (including `initialLookbackDays`) in `<workspaceRoot>/.nyssa-ai/daily-tasks/profile.json`.

### Out-of-band credentials

Enforce strict secret hygiene whenever standalone connectors or cloud vaults are configured:
- **Never** ask the user to paste a secret (OAuth client secret, Slack token, vault token, API key) into chat, and **never** pass a secret in tool arguments, Markdown, JSON profiles, or shell command lines.
- If the user pastes a secret into chat, do not echo it; instruct them to rotate the credential and capture the replacement out of band.
- Capture required secrets using one of two sanctioned paths:
  1. **Via MCP tool**: Call `daily_tasks_capture_secret(namespace, key, prompt_message?, provider?)`, inform the user that a local `127.0.0.1` loopback browser page has opened, and report the returned receipt (`namespace`, `key`, `provider`, `stored_at`).
  2. **Via user terminal**: Ask the user to run `daily_tasks.auth.secret` directly in their terminal (using `uv run` or `PYTHONPATH=<pluginRoot>/src python3`):
     - Gmail OAuth client (`communication/gmail-client-id` and `communication/gmail-client-secret`): `uv run python -m daily_tasks.auth.secret gmail` (add `--no-client-secret` for public clients).
     - Slack token (`communication/slack`): `uv run python -m daily_tasks.auth.secret slack`.
     - Cloud key vault (`bitwarden-secrets` / `bws` / `bitwarden`): `uv run python -m daily_tasks.auth.secret vault --name NAME --kind bitwarden-secrets --project-id ID`.
- For first-run interactive Gmail OAuth (`gmail.readonly`), ask the user to run `uv run python -m daily_tasks.auth.gmail --config-dir <userHome>/.nyssa-ai/daily-tasks` (or `PYTHONPATH=<pluginRoot>/src python3 -m daily_tasks.auth.gmail ...`) after storing the Gmail client credentials.

## Verification

Before reporting setup completion or continuing to a downstream workflow:
- [ ] Confirm the active harness (`OpenClaw`, `Antigravity`, `Claude Code`, `Claude Cowork`, `Codex`, `Cursor / Grok Bot`, or `Hermes Agent`) was explicitly identified and its native MCP/connector surface was used.
- [ ] Confirm the target `profile.json` exists on disk under `.nyssa-ai/daily-tasks/profile.json`, uses `schema_version: 2`, resolves an explicit IANA `timezone`, and contains no credentials or traversal paths.
- [ ] Confirm personal-only setup created no workspace bindings, workspace templates, project records, or project decision-log entries.
- [ ] Confirm workspace setup persisted `workspaceRoot`, `projectsRoot`, `dailyPlansRelative`, `sources` (with `initialLookbackDays`), and `templates`, placed/linked visible workspace templates with `templates/updates.json`, and verified live `daily_tasks_*` MCP tool availability (or halted cleanly if a harness session reload is required).
- [ ] Confirm the discovered Email/Chat connection inventory was rendered before prompting for connector choices, and only detected host integrations were offered as `Existing assistant connection (<discovered-integration-name>)`.
- [ ] Report the saved profile path(s), resolved IANA timezone, active harness MCP status, and template links to the user, then continue the original request only if all four setup gates are live.
