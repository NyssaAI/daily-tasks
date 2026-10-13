# Native Daily Tasks 0.5.0 recovery probe

Blocked before workflow writes: `operation-verify` returned exit 1, `INVALID_OPERATION`: `Invalid bound schemaV2 operation checkpoint`. The retained operation is legacy (no schemaVersion). `recover-operation` correctly found all five effects pending and no conflicts. The same read-only verification retry returned the identical error.

Checkpoint, plans, canonical records, baseline, historical plan, and rollover/removal state remain byte-identical. Log API reports zero events; no successful move or exactly-once event claim is made. No plugin repair or checkpoint relabeling was attempted.

Installed skills were discovered through native `skills_read`; resolved paths and SHA256 hashes, bounded before/after state, CLI errors, and host/session limitations are recorded in `native-recovery-evidence.json`. Node v24.19.0 on Linux. Exact astra model identity was not independently exposed; runtime identifies Codex/GPT-6. This is one blocked recovery probe, not nine workflow scenarios.
