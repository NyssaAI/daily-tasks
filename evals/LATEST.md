# Latest plugin evaluation

Generated from [matrix.json](matrix.json), [waza/skills/daily-tasks/eval.yaml](waza/skills/daily-tasks/eval.yaml), [waza/skills/daily-tasks/behavior.yaml](waza/skills/daily-tasks/behavior.yaml), and verified `.temp/evals/evidence/` receipts by `uv run python evals/report.py generate`.
Candidate SHA-256: `931456497b7c37828b08fe63e6500b7781c244ce0ec369549adf9515cdb1f251`. Suite revision: `0.11.3`.

A missing or failing required row blocks release. A consistent report does not imply release readiness.

Offline Waza trigger and behavioral definitions live in `evals/waza/skills/daily-tasks/` (see [README.md](README.md) for workflow instructions).

| Suite | Harness | Platform | Configuration | Required | Latest completed result | Outcome / score | Freshness | Newer attempt / next check |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| daily-tasks | Codex | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Codex session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Claude Code | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Claude Code session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Claude Cowork | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Claude Cowork session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Antigravity CLI | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Antigravity CLI session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Antigravity 2.0 | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Antigravity 2.0 session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Antigravity IDE | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Antigravity IDE session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Hermes Agent | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Hermes Agent session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | OpenClaw | windows-x86_64 | default | Yes | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated OpenClaw session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Cursor | windows-x86_64 | default | No | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Cursor session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Grok Bot | windows-x86_64 | default | No | Not run | Score unavailable | No result | Install staged bundle and verify MCP stdio launch, first-use setup, and daily-tasks scenarios in an isolated Grok Bot session outside repo_root; static validation, 18/18 offline Waza trigger tasks, and unit/use-case suites pass locally. |
| daily-tasks | Muse | windows-x86_64 | default | No | Not run | Score unavailable | No result | Provisional: establish loader contract before producing or validating an artifact. |

Release acceptance: **Fail — required evidence missing, stale, or failing**.
