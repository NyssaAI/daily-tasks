---
module: planning-cli
date: 2026-10-19
problem_type: performance_issue
component: planning_engine
severity: high
symptoms:
  - "Interactive 'plan my day' runs consume over 140 tool calls and 18 minutes on moderate vaults"
  - "PowerShell JSON parsing errors due to UTF-16LE BOM or truncated stdout buffers"
  - "Review screen validation rejection on valid carried tasks marked with ↺"
  - "CLI planning-prepare halted at create-plan state with empty rollover and task sources"
root_cause: logic_error
resolution_type: code_fix
tags:
  - planning
  - cli-contract
  - windows-bom
  - rollover
  - review-screen
  - legacy-migration
---

# Overcoming Planning Performance Degradation and Incomplete CLI Contracts

## Problem
During interactive daily planning on moderate-sized Obsidian vaults (~30–40 tasks), agent planning runs degraded into 140+ tool calls and over 18 minutes of wall-clock time. This was caused by an incomplete preparation contract in the CLI that forced client-side markdown traversal, Windows PowerShell stdout/BOM encoding corruption, review screen validation rejections on carried `↺` tasks, and dormant legacy migration checks.

## Symptoms
- Executing `daily-tasks-plan` for `"plan my day"` took ~140 tool calls, spending minutes traversing markdown files across vault project directories (`projectsRoot`) rather than reading pre-indexed tasks.
- On Windows systems, executing the CLI and capturing stdout via PowerShell redirection produced files containing UTF-16LE Byte Order Marks (`0xFF 0xFE`), causing subsequent CLI `--input` reads to crash with `SyntaxError: Unexpected token`.
- When today's plan file did not yet exist, `planning-prepare` returned `status: 'create-plan'` with empty `rollover.selected` and empty `taskSources`, leaving the LLM to deduce rollover candidates by reading raw task markdown files individually.
- Writing a daily plan with carried tasks prefixed with `↺` caused `savePlanningState` (`save-review`) to fail with `Review screen does not match the active template` because `carriedFrom` metadata was lost when parsing `↺` items back from disk.
- Audits and planning scans spent prompt tokens checking for obsolete `dod` (Definition of Done) files and testing for milestone workspace migrations.

## What Didn't Work
- **Piping CLI output through shell commands**: Attempting to redirect CLI stdout to a JSON file via PowerShell (`> plan.json` or `Out-File -Encoding utf8`) resulted in PowerShell writing UTF-16LE or UTF-8 with BOM, breaking strict JSON parsers expecting raw UTF-8.
- **Client-side LLM rollover synthesis**: Letting the agent discover and parse project files when `create-plan` returned empty rollover caused extreme prompt bloating and 60+ tool calls, often miscalculating task ownership or active selections.
- **Repeated markdown rewrites for screen validation**: When `validateReviewScreen` rejected the generated review screen because `carriedFrom` was missing on `↺` rows, the agent attempted multiple formatting edits (spacing, bullet styles, link escaping), none of which addressed the underlying metadata mismatch.

## Solution

### 1. Atomic File Output and BOM-Aware Decoding in the CLI
Added `--output <ABSOLUTE_FILE>` support and robust multi-encoding BOM decoding in [`src/cli/daily-tasks.mjs`](file:///D:/repos/NyssaAI/daily-tasks/src/cli/daily-tasks.mjs#L59-L63). The CLI directly writes formatted JSON to the specified path without passing through the shell buffer:

```javascript
// src/cli/daily-tasks.mjs:59-63
function decodeJsonBytes(bytes) {
  if (bytes.length >= 2 && bytes[0] === 0xFF && bytes[1] === 0xFE) return bytes.subarray(2).toString('utf16le');
  if (bytes.length >= 2 && bytes[0] === 0xFE && bytes[1] === 0xFF) return new TextDecoder('utf-16be').decode(bytes.subarray(2));
  return bytes.toString('utf8').replace(/^\uFEFF/,'');
}
```

### 2. Complete Projections in `planning-prepare`
Updated [`src/core/planning/session.mjs`](file:///D:/repos/NyssaAI/daily-tasks/src/core/planning/session.mjs#L79-L90) so that when today's plan is missing, `preparePlanning` generates a `proposedId` via UUIDv7, immediately resolves the previous daily plan, carries forward eligible tasks, computes `taskSources` hashes, and constructs the complete numbered `review` screen. The agent receives the entire plan payload in a single CLI turn:

```javascript
// src/core/planning/session.mjs:79-90
const planId = current.id ?? current.proposedId;
let previous = null;
let rollover = current.id ? planRollover({today,planId:current.id,userEmail:context.profile.user.email,
  currentRows:current.rows,state:rolloverState.value,records,inventory:indexed.inventory}) : {status:'missing-plan',selected:[],unresolved:[]};
if (rollover.status === 'due' || rollover.status === 'missing-plan') {
  const dates = (await names(context.dailyPlansRoot)).map(name => /^(\d{4}\.\d{2}\.\d{2})-daily-plan\.md$/.exec(name)?.[1])
    .filter(date => calendarDate(date) && date < today).sort();
  if (dates.length) previous = await dailyPlan(context,dates.at(-1));
  records = await selectedRecords(context,[current,previous],records,indexed.inventory.sources);
  rollover = planRollover({today,planId,userEmail:context.profile.user.email,
    currentRows:current.rows,state:current.id ? rolloverState.value : null,previousDate:previous?.date,previousRows:previous?.rows ?? [],records,inventory:indexed.inventory});
}
```

### 3. Preserving Provenance for `↺` Checklist Rows
Updated [`src/core/planning/planning.mjs`](file:///D:/repos/NyssaAI/daily-tasks/src/core/planning/planning.mjs#L63) so that `markCurrent` preserves or assigns `carriedFrom` on any row bearing the `↺` marker, ensuring the internal view matches the authored review screen:

```javascript
// src/core/planning/planning.mjs:63
const markCurrent = rows => rows.map(row => row.carried && !row.carriedFrom ? {...row,carriedFrom:previousDate ?? 'carried'} : row);
```

### 4. Eliminating Legacy Migration Paths
Purged standalone `dod` record handling, milestone workspace migration scripts, and profile `schema_version: 1` fallback paths across the codebase. Enforced `schema_version: 2` with `configurationSources` exclusively in [`src/core/profile/schema.mjs`](file:///D:/repos/NyssaAI/daily-tasks/src/core/profile/schema.mjs#L29-L45).

## Why This Works
- **Deterministic Offloading**: Moving rollover calculations and task source hashing into the compiled Node runtime eliminates dozens of redundant LLM tool calls. The agent transitions from manual data aggregator to consumer of an authoritative projection.
- **Binary I/O Isolation**: Providing explicit `--output` file writes avoids terminal emulator line-wrapping, console buffer limits, and PowerShell encoding heuristics on Windows.
- **Symmetric View Round-Tripping**: Preserving `carriedFrom` on `↺` rows ensures that reading back an authored plan file produces an identical model to the pre-authored state, allowing strict template validation to succeed on the first attempt.
- **Zero Migration Context Burden**: Removing deprecated migration code cleanses the agent's prompt context of irrelevant instructions and obsolete branching rules.

## Prevention
- **Avoid Half-Prepared States in Agent APIs**: When designing CLI commands or tool endpoints for agent workflows, never return intermediate or half-populated state objects that require the agent to manually synthesize data available to the runtime.
- **Enforce Dedicated File Channels for Structured Data**: In agent CLI tools, always provide `--output <path>` alongside stdout. Machine-readable outputs exceeding a few kilobytes must never rely on shell output redirection.
- **Validate Serialization Symmetry**: Ensure that any domain model with special serialization glyphs (like `↺`) preserves full metadata fidelity across `serialize(parse(text)) == text` cycles.
- **Prune Completed Migrations Aggressively**: Once a breaking schema change has been adopted, eliminate the backwards-compatibility translation code rather than maintaining it indefinitely.
