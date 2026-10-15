# Latest evaluation

Direct code and package checks are separate from native-host activation.

| Target / suite | Required | Platform / configuration | Result | Evidence / next check |
| --- | --- | --- | --- | --- |
| node-local / deterministic-v1 | Yes | win32/x64 / node-22-plus | pass; current | [2026-10-15T21-37-41-597Z-6516](results/2026-10-15T21-37-41-597Z-6516/result.json) |
| codex / workflow-v4 | Yes | win32/x64 / default | Not run / unverified | Register portable artifact in an isolated Codex profile, verify skill discovery and run scenarios. |
| claude-code / workflow-v4 | No | win32/x64 / default | Not run / unverified | Authenticate Claude Code; run with --plugin-dir artifacts/portable in isolated fixture and execute scenarios. |
| claude-cowork / workflow-v4 | No | win32/x64 / default | Not run / unverified | Upload zipped artifacts/cowork; verify skill discovery, Node availability and persistence in isolated fixture. |
| antigravity-2 / workflow-v4 | No | win32/x64 / default | Not run / unverified | Register artifacts/antigravity in 2.0 and execute scenarios. |
| antigravity-cli / workflow-v4 | No | win32/x64 / default | Not run / unverified | Use authenticated agy CLI with isolated plugin registration and execute scenarios. |
| antigravity-ide / workflow-v4 | No | win32/x64 / default | Not run / unverified | Register Antigravity artifact in IDE and execute scenarios. |
| cursor / workflow-v4 | No | win32/x64 / default | Not run / unverified | Install portable Cursor shim in isolated host and execute scenarios. |
| grok-bot / workflow-v4 | No | win32/x64 / default | Not run / unverified | Load Cursor-compatible package on demand and execute scenarios; no SessionStart. |
| hermes / workflow-v4 | No | linux/x64 / default | Not run / unverified | Enable generated native Hermes package; verify six skills and execute scenarios. |
| openclaw / workflow-v4 | No | linux/x64 / default | Not run / unverified | Native prewarm setup and execution are verified in isolated OpenClaw 2026.10.2; register the portable bundle and execute the workflow scenarios through an isolated active Gateway. |
| muse / workflow-v4 | No | win32/x64 / default | Not run / unverified | Obtain verified first-party loader/schema before claiming implementation or runtime support. |
| node-linux / deterministic-v1 | No | linux/x64 / node-22-plus | Not run / unverified | Run node evals/run.mjs on Linux x64. |
| node-macos / deterministic-v1 | No | darwin/arm64 / node-22-plus | Not run / unverified | Run node evals/run.mjs on macOS arm64. |

Release acceptance: **Incomplete**. Every required matrix row needs current, verified passing evidence.

Only the latest evaluation run is retained; older results and attempts have been removed.
