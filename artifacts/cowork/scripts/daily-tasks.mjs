#!/usr/bin/env node
import { readFile, readdir, lstat, realpath } from 'node:fs/promises';
import path from 'node:path';
import { uuid7 } from '../lib/identity/identity.mjs';
import { appendDecision, queryDecisions, archiveDecisions } from '../lib/log/decision-log.mjs';
import { parseRecord, validateRecords, checkClosure, checkLinks, recordMarkdownIsManaged } from '../lib/records/records.mjs';
import { reconcileRecord, reopenAncestors, recoverOperation } from '../lib/reconciliation/reconciliation.mjs';
import { activityTime, localDay, displayTime } from '../lib/time/time.mjs';
import { carryForward, parseChecklist, planRollover } from '../lib/planning/planning.mjs';
import { validateProfile } from '../lib/profile/profile.mjs';
import { resolveContext, assertPlanningScope } from '../lib/profile/context.mjs';
import { projectInventory, invalidateInventory } from '../lib/inventory/inventory.mjs';
import { planningReview, planSelection, maintenanceStatus } from '../lib/planning/review.mjs';

const operations = {
  'new-id': () => ({ id: uuid7() }),
  'activity-time': input => activityTime(input.reported, input.now),
  'local-day': input => ({ day: localDay(input.time || new Date().toISOString(), input.timezone) }),
  'format-time': input => ({ display: displayTime(input.time, input.timezone) }),
  'validate-profile': validateProfile,
  'resolve-context': resolveContext,
  'project-index': projectInventory,
  'invalidate-project-index': invalidateInventory,
  'planning-review': planningReview,
  'plan-selection': planSelection,
  'maintenance-status': maintenanceStatus,
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
      if (entry.isDirectory()) await visit(filename);
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
    console.log(JSON.stringify({ name: 'daily-tasks', version: '0.1.0', usage: 'node <installed-entry-path> OPERATION --input ABSOLUTE_JSON_FILE [--dry-run]', operations: Object.keys(operations),
      effects: 'Log operations mutate logs/locks; project-index and invalidate-project-index mutate disposable JSON cache. Markdown operations only inspect or propose.',
      scope: 'Explicit absolute projectsRoot for log/scan; explicit timezone for local displays. No environment variables or credentials.',
      exits: '0: JSON result (inspect diagnostics before applying). 1: JSON error on stderr.' }));
    return;
  }
  const operation = args.shift();
  if (!operations[operation]) throw new Error(`Unknown operation: ${operation}`);
  let inputPath;
  let dryRun = false;
  while (args.length) {
    const flag = args.shift();
    if (flag === '--input' && !inputPath) inputPath = args.shift();
    else if (flag === '--dry-run') dryRun = true;
    else throw new Error(`Unknown or duplicate argument: ${flag}`);
  }
  if (operation !== 'new-id' && (!inputPath || !path.isAbsolute(inputPath))) throw new Error('--input requires an absolute JSON file');
  const input = inputPath ? JSON.parse(await readFile(inputPath, 'utf8')) : {};
  if (!input || Array.isArray(input) || typeof input !== 'object') throw new Error('Input must be a JSON object');
  if (dryRun) input.dryRun = true;
  if (['planning-review','plan-selection','carry-forward','plan-rollover'].includes(operation)) assertPlanningScope(input);
  const result = await operations[operation](input);
  console.log(JSON.stringify(result));
}

main().catch(error => {
  console.error(JSON.stringify({ error: error.message, code: error.code || 'INVALID_OPERATION' }));
  process.exitCode = 1;
});
