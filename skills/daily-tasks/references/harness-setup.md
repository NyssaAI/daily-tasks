# Harness-aware setup and MCP registration

> [!IMPORTANT] Scope Directive
> This reference owns per-harness detection signals, runtime launcher resolution (`uv` vs. Python `>=3.12`), native MCP server registration syntax, privilege boundaries, and host connector discovery across OpenClaw, Google Antigravity, Claude Code, Claude Cowork, Codex, Cursor / Grok Bot, and Hermes Agent. It does NOT own the step-by-step setup execution checklist (owned by [`../workflows/setup.md`](../workflows/setup.md)) or MCP JSON-RPC tool schemas (owned by [`cli.md`](cli.md)).

## Harness identification

Daily Tasks runs across multiple agent harnesses with distinct MCP registration mechanisms, sandbox boundaries, and skill loaders. Before checking connectors or registering `daily-tasks-mcp`, Setup identifies the active harness from its live tool surface and environment rather than assuming a single CLI such as `agy`:

| Harness | Identification Signals | Skill Loader & Privilege Notes |
| :--- | :--- | :--- |
| **OpenClaw** | Code-mode `exec` with `catalog.search(...)` / `skills.read("daily-tasks")`, native `openclaw` CLI in `PATH`, or `OPENCLAW_STATE_DIR` Gateway environment | Load skills by skill name (`skills.read("daily-tasks")`), never by filesystem path. Agent turns run under an unprivileged service account; execute `openclaw mcp ...` via `exec` (or the `openclaw` delegation tool when exposed), never `sudo`. |
| **Google Antigravity** | `agy` CLI (`Antigravity 2.0`, `Antigravity CLI`, `Antigravity IDE`), `call_mcp_tool`, or `mcp_daily-tasks_*` tools | Project plugins live at `.agents/plugins/daily-tasks/` with `mcp_config.json`; CLI/user registration uses `agy mcp`. |
| **Claude Code** | `claude` CLI, `CLAUDE_PLUGIN_ROOT`, or `.claude-plugin/plugin.json` session context | Auto-discovers `.mcp.json` when loaded via `--plugin-dir` or approved in `claude mcp list`; manual registration uses `claude mcp add`. |
| **Claude Cowork** | Desktop/cloud Cowork plugin session without host CLI installers | Consumes bundled `.mcp.json` from the uploaded Cowork archive (`artifacts/cowork`); local stdio MCP requires desktop execution permission in Customize > Plugins. |
| **Codex** | `codex` CLI, `~/.codex/config.toml`, or `.codex-plugin/plugin.json` context | Auto-discovers portable `mcp.json` from installed plugin bundles or registers via `codex mcp add`. |
| **Cursor / Grok Bot** | `.cursor-plugin/plugin.json` or `.cursor/mcp.json` workspace context | Cursor reads installed plugin `mcp.json` or `<workspaceRoot>/.cursor/mcp.json`. Grok Bot shares `.cursor-plugin` packaging (`foundation-on-demand`, no `SessionStart` hooks) and requires verifying MCP tool availability before execution. |
| **Hermes Agent** | `hermes` CLI, `HERMES_ENABLE_PROJECT_PLUGINS`, or `~/.hermes/` runtime | Reads `mcp.json` in `.hermes/plugins/daily-tasks/` (when project plugins are enabled) or MCP declarations in `~/.hermes/config.yaml`. |

## Python runtime resolution

`daily-tasks-mcp` requires Python `>=3.12`. Resolve the launcher with a single non-recursive lookup (`where.exe uv` on Windows or `which uv` on POSIX) before constructing a host registration command:

1. **Preferred (`uv` available)**:
   - Command: `uv`
   - Arguments: `run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>`
2. **Fallback (`uv` unavailable, `python3` or `python` `>=3.12` with dependencies installed)**:
   - Environment: `PYTHONPATH=<pluginRoot>/src`
   - Command: `python3` (POSIX) or `python` (Windows)
   - Arguments: `-m daily_tasks.server --workspace-root <workspaceRoot>`

Always resolve `<pluginRoot>` from the real physical plugin directory (`realpath` on the loaded skill directory's `../..` parent when skills are symlinked, verifying `pyproject.toml` or `src/daily_tasks` exists there) and `<workspaceRoot>` from the bound absolute workspace path—never from `os.getcwd()`.

## Per-harness MCP server registration

When `daily_tasks_*` MCP tools are already callable in the current session (for example via self-contained `.mcp.json`, `mcp.json`, or `mcp_config.json` bundle discovery), skip manual registration and proceed directly to verification. Otherwise, register `daily-tasks` using the active harness's native surface:

### OpenClaw

- **From an interactive OpenClaw agent turn**: Run `openclaw mcp add` followed by `openclaw mcp reload` directly via shell `exec` (`await exec({ command: "openclaw mcp add ... && openclaw mcp reload" })` as the unprivileged service user—never `sudo`), or via the `openclaw` delegation tool when exposed. Always resolve symlinks (`realpath ~/plugin-skills/daily-tasks` -> `<pluginRoot>/skills/daily-tasks`) before computing `<pluginRoot>`.
- **CLI commands**:
  ```text
  # With uv:
  openclaw mcp add daily-tasks --command uv --arg run --arg --directory --arg <pluginRoot> --arg daily-tasks-mcp --arg --workspace-root --arg <workspaceRoot>
  openclaw mcp reload

  # With python3 (>=3.12) when uv is not installed:
  openclaw mcp add daily-tasks --command python3 --env PYTHONPATH=<pluginRoot>/src --arg -m --arg daily_tasks.server --arg --workspace-root --arg <workspaceRoot>
  openclaw mcp reload
  ```
- **Verification**: Run `openclaw mcp probe daily-tasks` and `catalog.search("daily_tasks")`, confirming `daily_tasks_start_session` and sibling tools are listed.

### Google Antigravity (`agy` CLI / IDE / 2.0)

`agy mcp add` requires flags (`--env`) before `<name>` and `--` before any command arguments starting with `-`:

```text
# With uv:
agy mcp add daily-tasks -- uv run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>

# With python3 (>=3.12):
agy mcp add --env "PYTHONPATH=<pluginRoot>/src" daily-tasks -- python3 -m daily_tasks.server --workspace-root <workspaceRoot>
```

### Claude Code and Claude Cowork

- **Claude Code**: If `.mcp.json` is shown as pending approval in `claude mcp list`, prompt the user to approve it; otherwise register via CLI:
  ```text
  # With uv:
  claude mcp add daily-tasks -- uv run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>

  # With python3 (>=3.12):
  claude mcp add daily-tasks -e PYTHONPATH=<pluginRoot>/src -- python3 -m daily_tasks.server --workspace-root <workspaceRoot>
  ```
- **Claude Cowork**: Cowork loads `.mcp.json` from the uploaded Cowork plugin bundle (`artifacts/cowork`). Do not invoke host CLI commands inside Cowork; if `daily_tasks_*` tools are unavailable, instruct the user to enable local plugin MCP execution under **Customize > Plugins** and wait for confirmation.

### Codex

```text
# With uv:
codex mcp add daily-tasks -- uv run --directory <pluginRoot> daily-tasks-mcp --workspace-root <workspaceRoot>

# With python3 (>=3.12):
codex mcp add --env PYTHONPATH=<pluginRoot>/src daily-tasks -- python3 -m daily_tasks.server --workspace-root <workspaceRoot>
```

### Cursor and Grok Bot

- **Cursor**: When bundle `mcp.json` is not already active from the Cursor plugin install, write or update `<workspaceRoot>/.cursor/mcp.json` (preserving unrelated `mcpServers` entries):
  ```json
  {
    "mcpServers": {
      "daily-tasks": {
        "command": "uv",
        "args": ["run", "--directory", "<pluginRoot>", "daily-tasks-mcp", "--workspace-root", "<workspaceRoot>"]
      }
    }
  }
  ```
  (Or `"command": "python3"`, `"args": ["-m", "daily_tasks.server", "--workspace-root", "<workspaceRoot>"]`, and `"env": {"PYTHONPATH": "<pluginRoot>/src"}` when `uv` is absent.)
- **Grok Bot**: Verify `daily_tasks_*` MCP tools are exposed in the session. If the hosted Grok Bot environment cannot spawn local stdio MCP servers, stop and report the exact host capability requirement rather than running unverified fallback workflows.

### Hermes Agent

Assemble or enable `.hermes/plugins/daily-tasks/` (`mcp.json` included) with `HERMES_ENABLE_PROJECT_PLUGINS` and `hermes plugins enable daily-tasks`, or add the `daily-tasks` stdio server entry (`command`, `args`, and optional `env.PYTHONPATH`) under `mcp_servers` in `~/.hermes/config.yaml`.

## Harness-aware connector discovery

During Setup Step 4, inspect existing Email (`gmail`, `outlook`) and Chat (`slack`, `teams`) integrations using the active harness's discovery surface before rendering the inventory table:

- **OpenClaw**: Query `catalog.search("gmail")`, `catalog.search("outlook")`, `catalog.search("slack")`, and `catalog.search("teams")` (plus enabled read-only OpenClaw channel/MCP integrations) without mutating or sending messages.
- **Antigravity / Claude / Codex / Cursor / Hermes**: Inspect the session's registered MCP servers and read-only connector tools exposed in the harness context (e.g., native Gmail/Slack MCP servers or Composio MCP tools, only when actually present).
- **Standalone credentials**: Check stored credential metadata (never secret values) under `<userHome>/.nyssa-ai/daily-tasks` / configured secret vaults.
