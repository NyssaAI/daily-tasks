import { readFile, readdir, lstat, mkdir, writeFile, rename, unlink } from 'node:fs/promises';
import path from 'node:path';
import { createHash, randomUUID } from 'node:crypto';
import { isDeepStrictEqual } from 'node:util';
import { resolveContext } from '../profile/context.mjs';
import { projectInventory } from '../inventory/inventory.mjs';
import { parseRecord } from '../records/records.mjs';
import { maintenanceStatus } from './review.mjs';
import { parseChecklist } from './planning.mjs';
import { inspectNavigation } from '../records/navigation.mjs';

const hash = bytes => bytes === null ? null : createHash('sha256').update(bytes).digest('hex');
const within = (root, target) => {
  const relative = path.relative(root, target);
  return relative === '' || (relative !== '..' && !relative.startsWith('..' + path.sep) && !path.isAbsolute(relative));
};

async function ordinary(filename) {
  let current = path.parse(filename).root;
  for (const part of filename.slice(current.length).split(path.sep).filter(Boolean)) {
    current = path.join(current, part);
    try { if ((await lstat(current)).isSymbolicLink()) throw new Error(`Symbolic path excluded: ${current}`); }
    catch (error) { if (error.code === 'ENOENT') return null; throw error; }
  }
  if (!(await lstat(filename)).isFile()) throw new Error(`Expected ordinary file: ${filename}`);
  return readFile(filename, 'utf8');
}

async function pending(context) {
  const directory = path.join(context.stateRoot, 'operations');
  try {
    // Check ancestors through an ordinary absent sentinel before listing state.
    await ordinary(path.join(directory, '.maintenance-path-check'));
    return (await readdir(directory)).filter(name => name.endsWith('.json')).sort();
  } catch (error) { if (error.code === 'ENOENT') return []; throw error; }
}

function baselinePath(context, filename) {
  if (!path.isAbsolute(filename) || ![context.projectsRoot, context.dailyPlansRoot].some(root => within(root, filename))) throw new Error('Baseline view is outside the bound projects/plans');
  const relative = path.relative(within(context.projectsRoot, filename) ? context.projectsRoot : context.dailyPlansRoot, filename);
  if (relative.split(path.sep).some(part => part.startsWith('.')) || !/\.md$/i.test(filename)) throw new Error('Baseline view must be visible Markdown, never a decision log');
  return filename;
}

async function navigationTargetsMatch(context, targets) {
  if (!Array.isArray(targets)) return false;
  const seen = new Set();
  for (const target of targets) {
    if (!target || typeof target.path !== 'string' || !path.isAbsolute(target.path) ||
        path.resolve(target.path) !== target.path || seen.has(target.path) ||
        !(target.sha256 === null || /^[a-f0-9]{64}$/.test(target.sha256 ?? ''))) return false;
    seen.add(target.path);
    const root = [context.projectsRoot, context.dailyPlansRoot].find(root => within(root, target.path));
    if (!root || path.relative(root, target.path).split(path.sep).some(part => part.startsWith('.')) ||
        (target.sha256 !== null && !/\.md$/i.test(target.path))) return false;
    try {
      let current = path.parse(target.path).root;
      for (const part of target.path.slice(current.length).split(path.sep).filter(Boolean)) {
        current = path.join(current, part);
        if ((await lstat(current)).isSymbolicLink()) return false;
      }
      if (!(await lstat(target.path)).isFile()) return false;
      if (target.sha256 !== null && hash(await readFile(target.path, 'utf8')) !== target.sha256) return false;
    } catch (error) {
      if (['ENOENT', 'ENOTDIR'].includes(error.code)) return false;
      throw error;
    }
  }
  return true;
}

/** Report inspection freshness separately from unavailable trusted worker evidence. */
export async function verifiedMaintenanceStatus(input, indexed) {
  const context = await resolveContext(input);
  if (!context.configured) return { fullReconcileDue: true, inspectionDue: true, reason: 'setup-required' };
  const inventory = indexed ?? await projectInventory({ ...context, dryRun: true });
  const filename = path.join(context.stateRoot, 'maintenance-inspection.json');
  const text = await ordinary(filename);
  let value;
  try { value = text === null ? null : JSON.parse(text.replace(/^\uFEFF/, '')); } catch { return { ...maintenanceStatus({ now: context.now }), inspectionDue: true, reason: 'invalid-maintenance-receipt' }; }
  const baseline = await ordinary(path.join(context.stateRoot, 'reconciliation.json'));
  const valid = value?.schemaVersion === 2 && value.execution?.kind === 'cli-inspection' &&
    value.execution.model === null && value.contextBinding === context.planningBinding &&
    value.sourcesHash === hash(JSON.stringify(inventory.inventory.sources)) && value.baselineHash === hash(baseline) &&
    await navigationTargetsMatch(context, value.navigationTargets) &&
    !Object.hasOwn(value, 'model') && !Object.hasOwn(value, 'executionEvidence') && !(await pending(context)).length;
  const inspection = maintenanceStatus({ now: context.now, lastFullReconcileAt: valid ? value.completedAt : undefined });
  return { ...maintenanceStatus({ now: context.now }), inspectionDue: inspection.fullReconcileDue,
    reason: 'trusted-worker-evidence-unavailable', inspectionReason: valid ? 'verified-cli-inspection' : 'missing-stale-or-untrusted-receipt', path: filename };
}

/** Record a broad CLI inspection; never advance a worker-success timestamp. */
export async function inspectMaintenance(input) {
  if (['verified', 'executionEvidence', 'worker', 'model', 'lastFullReconcileAt', 'receipt'].some(key => Object.hasOwn(input, key))) throw new TypeError('Caller-authored worker success is not accepted');
  const context = await resolveContext(input);
  if (!context.configured) throw new Error('Configured context required');
  const filename = path.join(context.stateRoot, 'maintenance-inspection.json');
  const before = await ordinary(filename);
  const baselineFile = path.join(context.stateRoot, 'reconciliation.json');
  const baselineText = await ordinary(baselineFile);
  const operations = await pending(context);
  const indexed = await projectInventory({ ...context, forceRefresh: true, dryRun: true });
  const diagnostics = indexed.inventory.diagnostics.filter(issue => issue.code !== 'noncanonical-filename' && issue.code !== 'cancelled-prerequisite');
  let planRoot;
  try { if ((await lstat(context.dailyPlansRoot)).isDirectory()) planRoot = context.dailyPlansRoot; }
  catch (error) { if (error.code !== 'ENOENT') throw error; }
  const navigation = await inspectNavigation({ projectsRoot: context.projectsRoot, dailyPlansRoot: planRoot });
  diagnostics.push(...navigation.diagnostics);
  if (operations.length) diagnostics.push({ code: 'pending-operations', paths: operations });
  let baseline;
  try { baseline = baselineText === null ? null : JSON.parse(baselineText.replace(/^\uFEFF/, '')); }
  catch { diagnostics.push({ code: 'invalid-reconciliation-baseline' }); }
  const records = new Map();
  for (const source of indexed.inventory.sources.filter(source => source.anchor === 'projectsRoot')) {
    const filename = path.resolve(context.projectsRoot, source.path);
    const text = await ordinary(baselinePath(context, filename));
    if (hash(text) !== source.sha256) throw new Error('Source changed during maintenance inspection');
    const record = parseRecord(text, filename);
    if (record.id) records.set(record.id, record);
  }
  if (!baseline?.records || typeof baseline.records !== 'object' || Array.isArray(baseline.records)) diagnostics.push({ code: 'missing-reconciliation-baseline' });
  else for (const [id, entry] of Object.entries(baseline.records)) {
    const record = records.get(id);
    if (!record || !entry?.canonical || typeof entry.canonical !== 'object' || Array.isArray(entry.canonical) || !entry?.views || typeof entry.views !== 'object' || Array.isArray(entry.views)) { diagnostics.push({ code: 'invalid-baseline-record', recordId: id }); continue; }
    for (const [field, expected] of Object.entries(entry.canonical)) if (!isDeepStrictEqual(record[field], expected)) diagnostics.push({ code: 'canonical-needs-reconciliation', recordId: id, field });
    for (const [filename, view] of Object.entries(entry.views)) {
      const actual = await ordinary(baselinePath(context, filename));
      if (!/^[a-f0-9]{64}$/.test(view?.hash ?? '') || hash(actual) !== view.hash) diagnostics.push({ code: 'view-needs-reconciliation', recordId: id, path: filename });
    }
  }
  if (baseline?.records) {
    const projections = [...records.values()].flatMap(record => (record.projections ?? []).map(row => ({ ...row, path: record.path })));
    for (const source of indexed.inventory.sources.filter(source => source.anchor === 'vaultRoot')) {
      const filename = path.resolve(context.vaultRoot, source.path);
      const text = await ordinary(baselinePath(context, filename));
      if (hash(text) !== source.sha256) throw new Error('Plan changed during maintenance inspection');
      projections.push(...parseChecklist(text).map(row => ({ ...row, path: filename })));
    }
    for (const row of projections) if (!baseline.records[row.id]?.views?.[row.path]) diagnostics.push({ code: 'view-needs-enrollment', recordId: row.id, path: row.path });
  }
  if (diagnostics.length) return { status: 'blocked', diagnostics, successAdvanced: false };
  const refreshed = await projectInventory({ ...context, forceRefresh: true, dryRun: true });
  if (!isDeepStrictEqual(indexed.inventory.sources, refreshed.inventory.sources) || hash(await ordinary(baselineFile)) !== hash(baselineText) || (await pending(context)).length || !(await navigationTargetsMatch(context, navigation.targets))) throw new Error('Maintenance sources/state changed; retry');
  const value = { schemaVersion: 2, contextBinding: context.planningBinding, completedAt: new Date().toISOString(),
    sourcesHash: hash(JSON.stringify(refreshed.inventory.sources)), baselineHash: hash(baselineText),
    navigationTargets: navigation.targets,
    execution: { kind: 'cli-inspection', model: null, checks: ['full-graph', 'navigation', 'active-views', 'baseline-fields', 'pending-operations'] } };
  if (input.dryRun) return { status: 'preview', path: filename, value, successAdvanced: false };
  await ordinary(path.join(context.stateRoot, '.maintenance-path-check'));
  await mkdir(context.stateRoot, { recursive: true });
  const temporary = `${filename}.${randomUUID()}.tmp`;
  try {
    await writeFile(temporary, JSON.stringify(value, null, 2) + '\n', { flag: 'wx' });
    if (hash(await ordinary(filename)) !== hash(before) || hash(await ordinary(baselineFile)) !== hash(baselineText) || (await pending(context)).length || !(await navigationTargetsMatch(context, navigation.targets))) throw new Error('Maintenance state changed before save; retry');
    await rename(temporary, filename);
  } finally { await unlink(temporary).catch(error => { if (error.code !== 'ENOENT') throw error; }); }
  return { status: 'inspected', path: filename, value, successAdvanced: false };
}
