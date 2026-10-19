#!/usr/bin/env node
import { readFile, readdir, lstat, realpath, mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { uuid7 } from '#core/identity/identity.mjs';
import { appendDecision, queryDecisions, archiveDecisions } from '#core/log/decision-log.mjs';
import { parseRecord, validateRecords, checkClosure, checkLinks, recordMarkdownIsManaged, recordDirectoryIsHoldingArea } from '#core/records/records.mjs';
import { reconcileRecord, reopenAncestors, recoverOperation } from '#core/reconciliation/reconciliation.mjs';
import { activityTime, localDay, displayTime } from '#core/time/time.mjs';
import { carryForward, parseChecklist, planRollover } from '#core/planning/planning.mjs';
import { validateProfile } from '#core/profile/profile.mjs';
import { resolveContext, assertPlanningScope } from '#core/profile/context.mjs';
import { projectInventory, invalidateInventory } from '#core/inventory/inventory.mjs';
import { planningReview, planSelection } from '#core/planning/review.mjs';
import { inspectMaintenance, verifiedMaintenanceStatus } from '#core/planning/maintenance.mjs';
import { verifyOperation, completeOperation, completeChangedRollover } from '#core/operations/verification.mjs';
import { inspectNavigation } from '#core/records/navigation.mjs';
import { nextRecordNumber } from '#core/records/numbering.mjs';
import { preparePlanning, savePlanningState } from '#core/planning/session.mjs';
import { prepareTemplates, saveTemplateState } from '#core/templates/templates.mjs';

const operations = {
  'health-check': healthCheck,
  'new-id': () => ({ id: uuid7() }),
  'activity-time': input => activityTime(input.reported, input.now),
  'local-day': input => ({ day: localDay(input.time || new Date().toISOString(), input.timezone) }),
  'format-time': input => ({ display: displayTime(input.time, input.timezone) }),
  'validate-profile': validateProfile,
  'resolve-context': resolveContext,
  'template-prepare': prepareTemplates,
  'template-state': saveTemplateState,
  'project-index': projectInventory,
  'invalidate-project-index': invalidateInventory,
  'planning-review': planningReview,
  'plan-selection': planSelection,
  'maintenance-status': verifiedMaintenanceStatus,
  'maintenance-inspect': inspectMaintenance,
  'operation-verify': verifyOperation,
  'operation-complete': completeOperation,
  'rollover-complete': completeChangedRollover,
  'inspect-navigation': inspectNavigation,
  'next-record-number': nextRecordNumber,
  'planning-prepare': preparePlanning,
  'planning-state': savePlanningState,
  'parse-record': input => parseRecord(input.markdown, input.path),
  'parse-checklist': input => ({ rows: parseChecklist(input.markdown) }),
  'validate-records': input => ({ diagnostics: validateRecords(input.records) }),
  'check-links': input => ({ diagnostics: checkLinks(input.records) }),
  'check-closure': input => checkClosure(input.recordId, input.records),
  'reconcile-record': input => reconcileRecord(input.base, input.current, input.views),
  'reopen-ancestors': input => reopenAncestors(input.records, input.changedIds),
  'recover-operation': input => recoverOperation(input.operation, input.actual),
  'carry-forward': input => carryForward(input.rows, input.records, input.userEmail, {inventory:input.inventory,today:input.today}),
  'plan-rollover': planRollover,
  'inspect-records': inspectRecords,
  'log-append': appendDecision,
  'log-query': queryDecisions,
  'log-archive': archiveDecisions,
};

function decodeJsonBytes(bytes) {
  if (bytes.length >= 2 && bytes[0] === 0xFF && bytes[1] === 0xFE) return bytes.subarray(2).toString('utf16le');
  if (bytes.length >= 2 && bytes[0] === 0xFE && bytes[1] === 0xFF) return new TextDecoder('utf-16be').decode(bytes.subarray(2));
  return bytes.toString('utf8').replace(/^\uFEFF/,'');
}

async function healthCheck(input) {
  const nodeMajor = parseInt(process.versions.node.split('.')[0], 10);
  if (nodeMajor < 22) throw new Error(`Node >= 22 required; current: ${process.version}`);
  if (!input || (!input.vaultRoot && !input.projectsRoot && !input.workspaceRoot && !input.configurationSources)) {
    return { status: 'ok', nodeVersion: process.version, environmentOnly: true };
  }
  const context = await resolveContext(input);
  if (!context.configured || context.preferenceOnly) {
    return { status: 'setup-required', nodeVersion: process.version, configured: false };
  }
  return {
    status: 'ok',
    nodeVersion: process.version,
    configured: true,
    timezone: context.timezone,
    localDate: context.localDate,
    projectsRoot: context.projectsRoot,
    dailyPlansRoot: context.dailyPlansRoot,
    stateRoot: context.stateRoot,
  };
}

async function inspectRecords(input) {
  if (typeof input.projectsRoot !== 'string' || !path.isAbsolute(input.projectsRoot)) throw new Error('projectsRoot must be absolute');
  const root = await realpath(input.projectsRoot);
  if ((await lstat(input.projectsRoot)).isSymbolicLink()) throw new Error('projectsRoot cannot be a symbolic link');
  const records = [];
  async function visit(directory) {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      if (entry.name.startsWith('.')) continue;
      const filename = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) throw new Error(`Symbolic link excluded: ${filename}`);
      if (entry.isDirectory()) {
        if (recordDirectoryIsHoldingArea(path.relative(root,filename))) continue;
        await visit(filename);
      }
      else if (entry.isFile() && /\.md$/i.test(entry.name)) {
        const text = await readFile(filename, 'utf8');
        if (recordMarkdownIsManaged(text,filename)) records.push(parseRecord(text, filename));
      }
    }
  }
  await visit(root);
  return { records, diagnostics: [...validateRecords(records), ...checkLinks(records)] };
}

async function main() {
  const args = process.argv.slice(2);
  if (args.length === 0 || args.includes('--help')) {
    let version;
    for (const rel of ['../../package.json', '../package.json']) {
      try { version = JSON.parse(await readFile(new URL(rel, import.meta.url), 'utf8')).version; break; } catch {}
    }
    console.log(JSON.stringify({ name: 'daily-tasks', version, usage: 'node <installed-entry-path> OPERATION --input ABSOLUTE_JSON_FILE [--output ABSOLUTE_JSON_FILE] [--dry-run]', operations: Object.keys(operations),
      effects: 'Log operations mutate logs/locks; inventory/preparation mutate cache; planning/operation completion saves verified JSON state and clears checkpoints. Template preparation is read-only; template-state retains JSON snapshots/choices and logs project decisions. Maintenance inspection records CLI checks, never worker success. Markdown operations only inspect or propose.',
      scope: 'Explicit absolute projectsRoot for log/scan; explicit timezone for local displays. No environment variables or credentials.',
      exits: '0: JSON result (inspect diagnostics before applying). 1: JSON error on stderr.' }));
    return;
  }
  const operation = args.shift();
  if (!operations[operation]) throw new Error(`Unknown operation: ${operation}`);
  let inputPath;
  let outputPath;
  let dryRun = false;
  while (args.length) {
    const flag = args.shift();
    if (flag === '--input' && !inputPath) inputPath = args.shift();
    else if (flag === '--output' && !outputPath) outputPath = args.shift();
    else if (flag === '--dry-run') dryRun = true;
    else throw new Error(`Unknown or duplicate argument: ${flag}`);
  }
  if (!['new-id','health-check'].includes(operation) && (!inputPath || !path.isAbsolute(inputPath))) throw new Error('--input requires an absolute JSON file');
  if (outputPath !== undefined && (!outputPath || !path.isAbsolute(outputPath))) throw new Error('--output requires an absolute JSON file');
  const input = inputPath ? JSON.parse(decodeJsonBytes(await readFile(inputPath))) : {};
  if (!input || Array.isArray(input) || typeof input !== 'object') throw new Error('Input must be a JSON object');
  if (dryRun) input.dryRun = true;
  if (['planning-review','plan-selection','carry-forward','plan-rollover'].includes(operation)) assertPlanningScope(input);
  const result = await operations[operation](input);
  const serialized = JSON.stringify(result);
  if (outputPath) {
    await mkdir(path.dirname(outputPath), { recursive: true });
    await writeFile(outputPath, `${JSON.stringify(result, null, 2)}\n`, 'utf8');
  }
  console.log(serialized);
}

main().catch(error => {
  console.error(JSON.stringify({ error: error.message, code: error.code || 'INVALID_OPERATION' }));
  process.exitCode = 1;
});
