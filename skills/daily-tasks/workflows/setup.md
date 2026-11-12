> [!IMPORTANT] Scope Directive
> This workflow owns harness-aware initial setup, legacy v1 migration, and explicit updates to Daily Tasks identity, timezone, priorities, storage bindings, MCP server registration, communication connectors, and out-of-band secret capture. It does NOT own candidate extraction (`capture.md`), record creation or repair (`records.md`), daily planning (`plan.md`), check-in reconciliation (`checkin.md`), or low-level tool/template schemas (owned by `../references/cli.md`, `../references/harness-setup.md`, and `../references/templates.md`).

# Set up Daily Tasks

Run this workflow on first use, whenever **any** mandatory setup gate is incomplete, or when the user explicitly requests a configuration change. **Let the deterministic MCP setup tools do the file work**:
1. Discover/activate `daily_tasks_*` MCP tools in the harness (`tool_search` / `catalog.search("daily_tasks")`).
2. Call `daily_tasks_setup_status(workspace_root="<authorizedVaultPath>")` to inspect v2 profiles, legacy `.nyssaai` v1 migration candidates, PARA vs. standard vault layout, and existing formatting templates in one read-only call.
3. Present discovered settings + the Email/Chat connector inventory table to the user and obtain **explicit confirmation** (never guess `"UTC"` or silently assume connector choices).
4. Call `daily_tasks_configure_workspace(confirmed=true, ...)` to atomically write Schema Version 2 `profile.json` files, seed missing templates without overwriting customized ones, and record `templates/updates.json`. **Never** hand-write `profile.json` or templates when `daily_tasks_configure_workspace` is callable.

Reference [harness setup](../references/harness-setup.md) for per-harness MCP discovery/registration, [MCP / CLI interface](../references/cli.md) for tool parameters, and [record conventions](../references/records.md) for output root rules.

## 1. Pre-flight, harness detection, and deterministic inspection

1. **Keep the user informed**: Announce each setup phase clearly (checking MCP tools and profiles, inspecting connectors, confirming settings, and persisting configuration). Never run silent multi-command probe loops.
2. **Identify the active harness and check live MCP tools first**:
   - Detect the current harness (`OpenClaw`, `Google Antigravity`, `Claude Code`, `Claude Cowork`, `Codex`, `Cursor / Grok Bot`, or `Hermes Agent`) per [harness setup](../references/harness-setup.md#harness-identification).
   - Check whether `daily_tasks_setup_status` and sibling `daily_tasks_*` MCP tools are already live (via `tool_search` / `catalog.search("daily_tasks")` when deferred tool loading is enabled). Most hosts auto-start the bundled server via `.mcp.json` / `mcp.json` (`src/daily_tasks/launch_mcp.py`). If not yet registered, complete Section 3 first.
3. **Bind the user's vault root (never an agent persona directory)**:
   - Pass the user's authorized absolute vault/workspace path as `workspace_root` (for example `/srv/vaults/<vault>` on a shared host).
   - **Never** bind `<pluginRoot>` or an agent persona runtime workspace containing `SOUL.md` and `IDENTITY.md` (such as `/var/lib/openclaw/workspace`) as a Daily Tasks vault.
   - If no user vault path is known and the request requires projects or daily plans, ask the user which absolute directory to bind as `workspaceRoot`.
4. **Inspect existing v2 and legacy v1 state via `daily_tasks_setup_status`**:
   - Call `daily_tasks_setup_status(workspace_root="<workspaceRoot>")` (or with no arguments for personal-only setup).
   - When `legacy_v1_detected` is `true` (`legacy_workspace_v1` / `legacy_user_v1`), present the discovered `user`, `timezone`, `priorities`, `projectsRoot`, and `dailyPlansRelative` values to the user and offer to migrate them into Schema Version 2 `.nyssa-ai/daily-tasks/profile.json` (leaving the legacy `.nyssaai` file untouched unless separate removal is authorized).
   - If `daily_tasks_setup_status` reports malformed JSON in any inspected file, stop and report the exact parse error and path without overwriting the file.
   - Select `"personal"` scope only when the user explicitly requests a personal-only setting with no workspace; otherwise use `"workspace"` scope (which also binds `defaultWorkspaceRoot` in user `profile.json` for zero-arg tool calls).

## 2. Harness-aware communication sources, identity, and confirmation

1. **Inventory Email and Chat connections** *(skip for personal-only setup)*:
   - Inspect Email (`gmail`, `outlook`) and Chat (`slack`, `teams`) integrations available in the **detected harness** per [harness connector discovery](../references/harness-setup.md#harness-aware-connector-discovery) plus stored standalone credentials in `<userHome>/.nyssa-ai/daily-tasks`.
   - **MUST** render a clear Markdown summary table of detected Email and Chat connections **before** prompting for choices:

     | Channel / Source | Discovered Host Connections / MCP Servers | Stored Standalone Credentials |
     | :--- | :--- | :--- |
     | **Email** (Gmail, Outlook) | `<e.g. OpenClaw/MCP integration name, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |
     | **Chat** (Slack, Teams) | `<e.g. OpenClaw/MCP integration name, or "None detected">` | `<e.g. Stored in local profile/secrets vault, or "None">` |

2. **Prompt once for missing or unconfirmed choices** *(never choose silently or treat silence as consent)*:
   - **Identity & timezone**: Reuse confirmed `user.name` and `user.email`; ask if missing or migrating from v1. Require an explicit IANA timezone (e.g. `"America/Chicago"`, never `"system"`). When `host_timezone_needs_user_confirmation` is `true` (for example on a `UTC` Linux server), ask the user to confirm their local IANA timezone and **never** silently write `"UTC"`. Update `priorities` only from explicit user statements or confirmed v1 migration.
   - **Storage & templates** *(workspace scope)*: Confirm `projects_root` and `daily_plans_relative` (`1-projects` and `2-areas/daily-plans` for PARA vaults; `projects` and `daily-plans` otherwise) and note any `discovered_existing_templates` that will be preserved untouched.
   - **Connectors & lookback** *(workspace scope)*: Offer **Existing assistant connection (`<discovered-integration-name>`)** *only* when actually detected in Step 1, **Standalone read-only connector**, or **Disabled** for Email/Chat, plus `initial_lookback_days` (default `7` days, positive integer).
3. **Persist deterministically via `daily_tasks_configure_workspace`**:
   - Once the user explicitly confirms, call `daily_tasks_configure_workspace` with `confirmed=true`, `scope`, `workspace_root`, `user_name`, `user_email`, `timezone`, `priorities`, `projects_root`, `daily_plans_relative`, `harness_connections`, `standalone_sources`, `disabled_sources`, and `initial_lookback_days`.
   - Verify `payload.setup_complete == true` (for workspace scope) and confirm connectivity with `daily_tasks_get_fetch_window(workspace_root="<workspaceRoot>")`.

## 3. Manual MCP registration fallback *(only when bundled MCP is not already live)*

1. **Do NOT re-register an active bundled server**:
   - Bundled `.mcp.json` / `mcp.json` / `mcp_config.json` launches `python3 <pluginRoot>/src/daily_tasks/launch_mcp.py` (which uses installed Python packages directly or falls back to `uv run`).
   - **OpenClaw**: OpenClaw's `bundle-mcp` loader starts `.mcp.json` automatically when the extension is enabled. Use `tool_search` (`query: "daily_tasks"`) to load `daily_tasks_*` tools. **Never** run `openclaw mcp add` or `openclaw mcp set` from shell while the OpenClaw Gateway service is active (offline state lock). If `daily_tasks_*` tools are unavailable, report the exact status to the operator instead of improvising shell workarounds.
2. **Register on CLI harnesses when needed** ([exact syntax](../references/harness-setup.md#per-harness-mcp-server-registration)):
   - **Google Antigravity**: `agy mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py`
   - **Claude Code / Cowork**: Approve `.mcp.json` in `claude mcp list` or run `claude mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py`; in Cowork, enable local plugin MCP execution under **Customize > Plugins** if blocked.
   - **Codex**: `codex mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py`
   - **Cursor / Grok Bot / Hermes**: Enable the bundled `mcp.json` or register `python3 <pluginRoot>/src/daily_tasks/launch_mcp.py` per [harness setup](../references/harness-setup.md); stop cleanly if a session reload is required.

### Out-of-band credentials

Enforce strict secret hygiene whenever standalone connectors or cloud vaults are configured:
- **Never** ask the user to paste a secret (OAuth client secret, Slack token, vault token, API key) into chat, and **never** pass a secret in tool arguments, Markdown, JSON profiles, or shell command lines.
- If the user pastes a secret into chat, do not echo it; instruct them to rotate the credential and capture the replacement out of band.
- Capture required secrets using one of two sanctioned paths:
  1. **Via MCP tool**: Call `daily_tasks_capture_secret(namespace, key, prompt_message?, provider?)`, inform the user that a local `127.0.0.1` loopback browser page has opened, and report the returned receipt (`namespace`, `key`, `provider`, `stored_at`).
  2. **Via user terminal**: Ask the user to run `daily_tasks.auth.secret` directly in their terminal (`uv run python -m daily_tasks.auth.secret gmail|slack|vault ...` or `PYTHONPATH=<pluginRoot>/src python3 -m daily_tasks.auth.secret ...`), followed by `python -m daily_tasks.auth.gmail --config-dir <userHome>/.nyssa-ai/daily-tasks` for first-run interactive Gmail OAuth (`gmail.readonly`).

## Verification

Before reporting setup completion or continuing to a downstream workflow:
- [ ] Confirm the active harness was identified, `daily_tasks_setup_status` was inspected, and no agent persona workspace (`SOUL.md` + `IDENTITY.md`) was bound as `workspaceRoot`.
- [ ] Confirm the discovered Email/Chat connection inventory (and any legacy `.nyssaai` v1 values) was presented to the user and explicit confirmation was obtained before calling `daily_tasks_configure_workspace(confirmed=true, ...)`.
- [ ] Confirm personal-only setup (`scope="personal"`) created no workspace bindings, workspace templates, or project files.
- [ ] Confirm workspace setup (`scope="workspace"`) persisted Schema Version 2 `profile.json` with an explicit IANA `timezone`, preserved any existing customized templates, recorded `templates/updates.json`, and passed `daily_tasks_setup_status` (`setup_complete: true`).
- [ ] Report the saved profile path(s), resolved IANA timezone, active harness MCP status, and template links to the user, then continue the original request only if all four setup gates are live.
