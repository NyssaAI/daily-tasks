# Latest evaluation

Direct code and package checks are separate from native-host activation.

| Target / suite | Platform / configuration | Result | Evidence / next check |
| --- | --- | --- | --- |
| node-local / deterministic-v1 | win32/x64 / node-22-plus | pass; current | [2026-10-05T20-38-01-538Z-40428](results/2026-10-05T20-38-01-538Z-40428/result.json) |
| codex / workflow-v1 | win32/x64 / default | Not run / unverified | Register portable artifact in an isolated Codex profile, verify skill discovery and run scenarios. |
| claude-code / workflow-v1 | win32/x64 / default | Not run / unverified | Authenticate Claude Code; run with --plugin-dir artifacts/portable in isolated fixture and execute scenarios. |
| claude-cowork / workflow-v1 | win32/x64 / default | Not run / unverified | Upload zipped artifacts/cowork; verify skill discovery, Node availability and persistence in isolated fixture. |
| antigravity-2 / workflow-v1 | win32/x64 / default | Not run / unverified | Register artifacts/antigravity in 2.0 and execute scenarios. |
| antigravity-cli / workflow-v1 | win32/x64 / default | Not run / unverified | Use authenticated agy CLI with isolated plugin registration and execute scenarios. |
| antigravity-ide / workflow-v1 | win32/x64 / default | Not run / unverified | Register Antigravity artifact in IDE and execute scenarios. |
| cursor / workflow-v1 | win32/x64 / default | Not run / unverified | Install portable Cursor shim in isolated host and execute scenarios. |
| grok-bot / workflow-v1 | win32/x64 / default | Not run / unverified | Load Cursor-compatible package on demand and execute scenarios; no SessionStart. |
| hermes / workflow-v1 | linux/x64 / default | Not run / unverified | Enable generated native Hermes package; verify six skills and execute scenarios. |
| openclaw / workflow-v1 | linux/x64 / default | Not run / unverified | Register portable bundle, verify winning format and run scenarios through active Gateway. |
| muse / workflow-v1 | win32/x64 / default | Not run / unverified | Obtain verified first-party loader/schema before claiming implementation or runtime support. |
| node-linux / deterministic-v1 | linux/x64 / node-22-plus | Not run / unverified | Run node evals/run.mjs on Linux x64. |
| node-macos / deterministic-v1 | darwin/arm64 / node-22-plus | Not run / unverified | Run node evals/run.mjs on macOS arm64. |

Release acceptance: **Incomplete**. Every required matrix row needs current, verified passing evidence.

Older development receipts without matrix coordinates are retained but do not establish acceptance.

Incomplete attempts and independent evaluation receipts are retained in [attempts/](attempts/).
