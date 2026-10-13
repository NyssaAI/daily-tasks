# Daily Tasks plugin repair plan

**Type:** Operations
**Status:** Validation in progress; one user decision pending
**Created:** 2026-10-13
**Origin:** `plans/brainstorm-daily-tasks-plugin-repair.md`

## Trigger

Execute after the 2026-10-13 diagnosis confirmed that discovery is fixed but navigation, maintenance evidence, live reconciliation, legacy enrollment, and release verification remain incomplete.

## Steps

1. Freeze the baseline: record source, installed artifact, host version, current tests, findings, and acceptance checks.
2. Run the maintained adversary instructions against the baseline and reconcile any new material findings.
3. In parallel, assign independent canonical-source code repairs to Sol 6.1 workers:
   - distinguish valid directory navigation from required file evidence;
   - close or explicitly disposition the trusted worker-evidence integration gap.
4. Integrate each repair separately, run focused acceptance checks, regenerate artifacts, and update the durable review.
5. Reconcile canonical/view conflicts and duplicate future-day allocations through Daily Tasks operations; preserve unrelated planning.
6. Migrate the two diagnosed legacy projects through the legacy-project workflow, preserving one canonical project identity and navigation per project.
7. Re-run full tests, assembly validation, installed-artifact probes, and report checks against version 0.5.0.
8. Run a fresh adversarial review, then the maintained final eval agent as the last quality gate.
9. Record remaining external host/platform blockers without relabeling stale evidence as current.

## Acceptance checks

- Existing directory navigation links pass; nonexistent file evidence still fails.
- Maintenance output distinguishes inspection freshness from trusted worker completion and does not globally block independent planning.
- No unresolved view-state differences or duplicate October 14/15 allocations remain for the affected task IDs.
- Each legacy project has exactly one managed `project-index.md`, valid UUIDv7 metadata, preserved content, resolvable navigation, and a verified decision-log entry.
- Generated artifacts match canonical source; the installed plugin resolves to the new artifact and current package version.
- All runnable tests and available native eval rows execute; unavailable required rows remain explicit release blockers.

## Edge Cases

| Situation | What to do |
| --- | --- |
| Missing resume attachment is real | Preserve the diagnostic; do not create or suppress evidence. |
| Conflicting task edits cannot be safely inferred | Leave only that task pending and continue independent work. |
| Legacy project contains ambiguous accepted scope | Preserve content and stop before inventing tasks or DoD. |
| Windows/native host unavailable | Save a durable attempt receipt and exact next check. |

## Owner

Jeremy Maynor owns acceptance. Tigan integrates and verifies. Sol 6.1 workers implement bounded code changes. Independent adversary/eval workers own their receipts.

## Dependencies

- Repository: `/srv/agent-work/openclaw/projects/daily-tasks`
- Vault: authorized live vault (path omitted from the public receipt)
- Installed OpenClaw 2026.10.2
- Daily Tasks operation, record, planning, and legacy-project contracts

## Success Metrics

| Metric | Current Baseline | Target | Source |
| --- | --- | --- | --- |
| Navigation false positives | 9 directory-link warnings | 0 | `check-links` output |
| Current view discrepancies | 5 across 4 tasks | 0 unresolved safe deltas | `maintenance-inspect` |
| Duplicate future allocations | 3 tasks | 0 | daily-plan inspection |
| Canonical legacy projects | 0 of 2 | 2 of 2 | `inspect-records` |
| Generated files matching | 218 | all generated files | `assemble.mjs check` |
| Release acceptance | incomplete | pass, or exact external blockers | `evals/report.mjs` and final eval receipt |

## Open Questions

- Trusted worker evidence requires an OpenClaw-native adapter; the portable plugin now reports that capability as explicitly unsupported instead of perpetually due.
- Whether a current Windows runner is available for the required release row.

## References

- `docs/2026.10.12-plugin-review.md`
- `docs/2026.10.13-plugin-review.md`
- `evals/LATEST.md`

## Execution Log

### 2026-10-13 Baseline
- Baseline inspection started against source revision `7d0e887` and package version 0.4.0.
- OpenClaw 2026.10.2 discovers the installed portable artifact as enabled, activated, and loaded.
- Assembly and static validation pass for 218 generated files and six skills.
- Full suite completed: 198 passed, 1 skipped, 0 failed.
- Astra Medium baseline adversary reproduced four findings and saved `docs/2026.10.13-plugin-review-adversarial.md`.

### 2026-10-13 Batch 1: independent code repairs
- Navigation/directory and vault-root maintenance target repair delegated to Sol 6.1 run `87e353ce-406a-4f43-a724-a327f6216046`.
- Migration backlink safety repair delegated to Sol 6.1 run `e8b91577-6c65-41da-af23-8dc1d57f873e`.
- Worker-evidence capability contract delegated to Sol 6.1 run `7ec5f9ef-9d89-463f-b89c-503cb7b83275`.

### 2026-10-13 Batch 2: integration and live reconciliation
- Integrated the explicit unsupported-worker disposition as commit `0c23607`.
- Integrated the combined navigation, maintenance-freshness, and migration-backlink series as commits `9cad0dc`, `10a2670`, and `956071d`.
- Combined focused verification passed 47/47 tests.
- Reconciled three safe project-view differences and removed the three duplicate October 14 allocations through verified operation `01a13565-3638-7aad-8491-25637f13ff52`.
- Preserved one contradictory completed/not-started record for explicit user resolution; did not establish a misleading baseline.
- Enrolled the two legacy projects with canonical UUIDv7 project records and retained legacy pointers through verified operation `01a13565-37f0-73d3-9205-4c75c53afcce`; no legacy checkbox became an accepted task.

### 2026-10-13 Batch 3: 0.5.0 candidate
- Bumped all host manifests once to 0.5.0 and regenerated 218 artifact files.
- Assembly check and six-skill executable validation passed.
- Full suite passed: 218 passed, 1 Windows-only skip, 0 failed.
- Refreshed the existing linked install; OpenClaw 2026.10.2 discovers version 0.5.0 as enabled, activated, loaded, and diagnostic-free.
- Final Astra Medium adversarial review started as run `4490684a-8d72-4c38-8352-b7638832d091`.
