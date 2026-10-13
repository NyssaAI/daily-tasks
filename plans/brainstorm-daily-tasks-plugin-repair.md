# Daily Tasks plugin repair brainstorm

**Origin:** Astra diagnosis completed 2026-10-13 and the existing 2026.10.12 plugin review.

## What I Heard

**The problem:** Daily Tasks now discovers in-scope work correctly, but maintenance still mixes canonical-data conflicts, legacy enrollment gaps, navigation false positives, and incomplete release evidence.

**Decisions already made:**
- Preserve all-owner planning discovery.
- Continue independent planning when only unrelated records are conflicted.
- Migrate legacy projects without duplicate managed project records.
- Treat existing holding-area directories as valid navigation targets while retaining strict checks for required file evidence.
- Keep trusted worker completion separate from ordinary CLI inspection freshness.
- Use Sol 6.1 subagents for bounded coding work and independent reviewers for release gates.

**Constraints:**
- Preserve user-authored vault content and unrelated repository changes.
- Use the Daily Tasks operation protocol for consequential vault writes.
- Keep personal vault content out of the public repository and evaluation receipts.
- Windows and some native harnesses may remain external verification blockers.
- The repository is already one unpushed commit ahead of `origin/main`.

**Known findings:**
1. Nine links to existing `outputs/` directories are falsely rejected.
2. Trusted worker-completion evidence has no host adapter and must not masquerade as inspection freshness.
3. Four task identities have five view-state discrepancies; three tasks are allocated on both October 14 and October 15.
4. Two diagnosed legacy projects are not canonical Daily Tasks records.
5. Three resume attachments are genuinely absent.
6. Windows, Codex-native, and OpenClaw-native release evidence is stale or missing.

## Themes and tensions

- **Behavior versus evidence:** installed behavior works better than the release report proves.
- **Navigation versus evidence:** directory navigation is valid, while links claiming a specific attachment must still resolve to a file.
- **Migration versus duplication:** legacy content must be preserved under one canonical project record.
- **Scoped conflicts versus global availability:** affected records pause; independent work remains usable.

## Direction

Repair one finding at a time with explicit acceptance checks, then reconcile the live vault through the plugin's operation protocol. Finish with a fresh adversarial review and final evaluation against the exact assembled candidate.
