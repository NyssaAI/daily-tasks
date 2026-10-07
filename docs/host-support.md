# Package and execution coverage

Source authored once under skills/, executable once under lib/ and bin/. No startup
foundation or autonomous agent. Node >=22 and filesystem/process access are required
for durable operations; unavailable runtimes can only discuss proposals.

| Host | Artifact / activation route | Runtime evidence |
| --- | --- | --- |
| Codex | portable root and generated .codex-plugin overlay; marketplace registration | See evals/LATEST.md; package validation alone is not activation |
| Codex Windows with phone access | Windows app hosts the vault/Node/plugin; phone connects to that host | Local CLI/packaging tests do not verify pairing or native skill activation |
| Claude Code | portable .claude-plugin; isolated `claude --plugin-dir <artifact>` | See evals/LATEST.md |
| Claude Cowork | artifacts/cowork, CLI moved to scripts/; zip this directory for upload | UI/Node/filesystem capabilities require verification |
| Antigravity 2.0 / CLI / IDE | artifacts/antigravity minimal manifest; install/register through selected surface | Each surface needs independent runtime verification |
| Cursor / Grok Bot | portable .cursor-plugin and skills/ | Grok has no SessionStart; on-demand only, runtime unverified |
| Hermes | artifacts/hermes plugin.yaml and generated register(ctx); enable project plugins or personal plugin explicitly | Runtime unverified |
| OpenClaw | portable compatible bundle; verify detected format and enable | Runtime unverified |
| Muse | Source inventory only | Provisional; no verified loader/schema, not supported runtime |

Local source build: `node scripts/assemble.mjs write`. Copies contain only runtime
content, no mutable evaluation results or user data. `check` detects drift/extras.
Python is needed only by the Hermes registration adapter. No bundled platform binaries;
portable Node source is used on Windows/Linux/macOS. CI validates available runners;
do not infer ARM/native-host support from x64 CLI tests. No MCP server is claimed.

Checked official packaging sources 2026-10-05:
[Codex](https://developers.openai.com/plugins/build/plugins),
[Claude](https://code.claude.com/docs/en/plugins-reference),
[Antigravity](https://antigravity.google/docs/plugins),
[Cursor](https://cursor.com/docs/reference/plugins),
[Hermes](https://hermes-agent.nousresearch.com/docs/developer-guide/plugins),
[OpenClaw](https://docs.openclaw.ai/plugins/bundles).
UUIDv7 follows [RFC 9562](https://www.rfc-editor.org/rfc/rfc9562.html#name-uuid-version-7).
