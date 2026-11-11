# Harness-aware setup and MCP registration

> [!IMPORTANT] Scope Directive
> This reference owns per-harness detection signals, portable launcher behavior (`src/daily_tasks/launch_mcp.py`), native MCP server registration syntax, privilege boundaries, and host connector discovery across OpenClaw, Google Antigravity, Claude Code, Claude Cowork, Codex, Cursor / Grok Bot, and Hermes Agent. It does NOT own the step-by-step setup execution checklist (owned by [`../workflows/setup.md`](../workflows/setup.md)) or MCP JSON-RPC tool schemas (owned by [`cli.md`](cli.md)).

## Harness identification

Daily Tasks runs across multiple agent harnesses with distinct MCP discovery mechanisms, sandbox boundaries, and skill loaders. Identify the active harness from its live tool surface and environment rather than assuming a single CLI such as `agy`:

| Harness | Identification Signals | Skill Loader & Privilege Notes |
| :--- | :--- | :--- |
| **OpenClaw** | `skills_read` / `tool_search` (or Code-mode `catalog.search(...)`), `OPENCLAW_STATE_DIR` Gateway environment | Load skills via `skills_read` or `/var/lib/openclaw/plugin-skills/daily-tasks/SKILL.md` (`~` is `/var/lib/openclaw`, never `/home/openclaw`). Bundled `.mcp.json` auto-starts via `bundle-mcp`; discover `daily_tasks_*` tools with `tool_search`. Never use `sudo` or run `openclaw mcp add`/`set` while the Gateway daemon holds offline state lock. |
| **Google Antigravity** | `agy` CLI (`Antigravity 2.0`, `Antigravity CLI`, `Antigravity IDE`), `call_mcp_tool`, or `mcp_daily-tasks_*` tools | Project plugins live at `.agents/plugins/daily-tasks/` with `mcp_config.json`; CLI/user registration uses `agy mcp`. |
| **Claude Code** | `claude` CLI, `CLAUDE_PLUGIN_ROOT`, or `.claude-plugin/plugin.json` session context | Auto-discovers `.mcp.json` when loaded via `--plugin-dir` or approved in `claude mcp list`; manual registration uses `claude mcp add`. |
| **Claude Cowork** | Desktop/cloud Cowork plugin session without host CLI installers | Consumes bundled `.mcp.json` from the uploaded Cowork archive (`artifacts/cowork`); local stdio MCP requires desktop execution permission in Customize > Plugins. |
| **Codex** | `codex` CLI, `~/.codex/config.toml`, or `.codex-plugin/plugin.json` context | Auto-discovers portable `mcp.json` from installed plugin bundles or registers via `codex mcp add`. |
| **Cursor / Grok Bot** | `.cursor-plugin/plugin.json` or `.cursor/mcp.json` workspace context | Cursor reads installed plugin `mcp.json` or `<workspaceRoot>/.cursor/mcp.json`. Grok Bot shares `.cursor-plugin` packaging and requires verifying MCP tool availability before execution. |
| **Hermes Agent** | `hermes` CLI, `HERMES_ENABLE_PROJECT_PLUGINS`, or `~/.hermes/` runtime | Reads `mcp.json` in `.hermes/plugins/daily-tasks/` (when project plugins are enabled) or MCP declarations in `~/.hermes/config.yaml`. |

## Portable Python MCP launcher (`launch_mcp.py`)

All bundled MCP manifests (`.mcp.json`, portable `mcp.json`, and Antigravity `mcp_config.json`) invoke `python3 <pluginRoot>/src/daily_tasks/launch_mcp.py`:
1. **In-process Python `>=3.12` fast path**: Prepends `<pluginRoot>/src` to `sys.path` in-process (avoiding host `PYTHONPATH` environment filters) and starts `daily_tasks.cli:cli` directly when runtime dependencies are installed in the active Python environment.
2. **Automatic `uv` fallback**: When `python3` lacks installed package dependencies and `uv` is available on `PATH`, execs `uv run --directory <pluginRoot> daily-tasks-mcp` automatically.
3. **Zero-arg startup + setup-gated mode**: The MCP server boots cleanly without `--workspace-root`, immediately exposing `daily_tasks_setup_status` and `daily_tasks_configure_workspace` while failing closed on session/fetch tools until Schema Version 2 setup is completed. Once `daily_tasks_configure_workspace` binds `defaultWorkspaceRoot` in `~/.nyssa-ai/daily-tasks/profile.json`, zero-arg `daily_tasks_start_session` and `daily_tasks_get_fetch_window` calls resolve that vault automatically.

Always resolve `<pluginRoot>` from the physical installed plugin directory (`realpath` on the loaded skill directory's `../..` parent when skills are symlinked) and `<workspaceRoot>` from the user's authorized vault path—never from `os.getcwd()` or an agent persona directory (`SOUL.md` + `IDENTITY.md`).

## Per-harness MCP server registration

When `daily_tasks_*` MCP tools are already callable in the current session (including via `tool_search` / `call_mcp_tool`), skip manual registration entirely and call `daily_tasks_setup_status`. Otherwise, use the active harness's native surface:

### OpenClaw

- **Bundled auto-discovery (`bundle-mcp`)**: Enabling the `daily-tasks` extension in OpenClaw automatically loads `.mcp.json` (`python3 ${CLAUDE_PLUGIN_ROOT}/src/daily_tasks/launch_mcp.py`). When `tools.toolSearch` is active, call `tool_search` with `"daily_tasks"` (or `catalog.search("daily_tasks")` in Code Mode) to surface `daily_tasks_setup_status`, `daily_tasks_configure_workspace`, `daily_tasks_start_session`, and sibling tools.
- **Offline lock constraint**: Do **not** run `openclaw mcp add` or `openclaw mcp set` from a shell tool while `openclaw.service` / Gateway is running; OpenClaw rejects live CLI mutations to state root MCP config (`requires exclusive offline state ownership`). Do not inject custom `mcpServers` overrides pointing at `/var/lib/openclaw/workspace`.

### Google Antigravity (`agy` CLI / IDE / 2.0)

```text
agy mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py
```

### Claude Code and Claude Cowork

- **Claude Code**: Approve `.mcp.json` if listed as pending in `claude mcp list`, or register manually:
  ```text
  claude mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py
  ```
- **Claude Cowork**: Cowork loads `.mcp.json` from the uploaded Cowork plugin bundle (`artifacts/cowork`). Do not invoke host CLI commands inside Cowork; if `daily_tasks_*` tools are unavailable, instruct the user to enable local plugin MCP execution under **Customize > Plugins** and wait for confirmation.

### Codex

```text
codex mcp add daily-tasks -- python3 <pluginRoot>/src/daily_tasks/launch_mcp.py
```

### Cursor, Grok Bot, and Hermes Agent

- **Cursor**: When bundle `mcp.json` is not already active from the Cursor plugin install, add `"daily-tasks": {"command": "python3", "args": ["<pluginRoot>/src/daily_tasks/launch_mcp.py"]}` under `mcpServers` in `<workspaceRoot>/.cursor/mcp.json`.
- **Grok Bot**: Verify `daily_tasks_*` MCP tools are exposed in the session; if local stdio MCP is unsupported by the host environment, stop and report the exact capability requirement.
- **Hermes Agent**: Enable `.hermes/plugins/daily-tasks/` (`HERMES_ENABLE_PROJECT_PLUGINS` and `hermes plugins enable daily-tasks`), or register `python3 <pluginRoot>/src/daily_tasks/launch_mcp.py` under `mcp_servers` in `~/.hermes/config.yaml`.

## Harness-aware connector discovery

Before calling `daily_tasks_configure_workspace`, inspect existing Email (`gmail`, `outlook`) and Chat (`slack`, `teams`) integrations using the active harness's discovery surface and render the inventory table first:

- **OpenClaw**: Query `tool_search` (or `catalog.search` in Code Mode) for `"gmail"`, `"outlook"`, `"slack"`, and `"teams"` read-only integrations without mutating or sending messages.
- **Antigravity / Claude / Codex / Cursor / Hermes**: Inspect the session's registered MCP servers and read-only connector tools exposed in the harness context (only offering an integration when actually present).
- **Standalone credentials**: Check stored credential metadata (never secret values) under `<userHome>/.nyssa-ai/daily-tasks` / configured secret vaults.
