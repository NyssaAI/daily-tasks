import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, stat, unlink } from 'node:fs/promises';
import path from 'node:path';
import { inspectMaintenance, verifiedMaintenanceStatus } from '../lib/planning/maintenance.mjs';

async function fixture() {
  await mkdir('.temp', { recursive: true });
  const vaultRoot = await mkdtemp(path.resolve('.temp/maintenance-'));
  const stateRoot = path.join(vaultRoot, '.nyssaai/daily-tasks');
  const projectsRoot = path.join(vaultRoot, '1-projects');
  await mkdir(path.join(projectsRoot, 'alpha'), { recursive: true });
  await mkdir(stateRoot, { recursive: true });
  await mkdir(path.join(vaultRoot, '2-areas/daily-plans'), { recursive: true });
  await writeFile(path.join(stateRoot, 'profile.json'), JSON.stringify({ schema_version: 1,
    user: { name: 'Owner', email: 'owner@example.test' }, timezone: 'America/Chicago', priorities: [],
    vaultRoot: './', projectsRoot: './1-projects', dailyPlansRelative: '2-areas/daily-plans' }));
  const project = path.join(projectsRoot, 'alpha/project-index.md');
  await writeFile(project, '---\nid: 019a1234-5678-7abc-8def-000000000001\ntype: project\ntitle: Alpha\nowner: owner@example.test\nproject-state: not-started\ncreated_at: 2026-10-06T14:00:00.000Z\nupdated_at: 2026-10-06T14:00:00.000Z\n---\n# Alpha\n');
  await writeFile(path.join(stateRoot, 'reconciliation.json'), JSON.stringify({ schemaVersion: 1, records: {} }));
  return { vaultRoot, stateRoot, projectsRoot, project };
}

test('CLI inspection freshness stays separate from worker success and follows source changes', async () => {
  const input = await fixture();
  const result = await inspectMaintenance(input);
  assert.equal(result.status, 'inspected');
  assert.deepEqual(result.value.execution.model, null);
  assert.equal((await verifiedMaintenanceStatus(input)).fullReconcileDue, true);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
  await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\nNew note.\n');
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await inspectMaintenance(input);
  await writeFile(path.join(input.stateRoot, 'reconciliation.json'), JSON.stringify({ schemaVersion: 1, records: {}, changed: true }));
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
});

test('unsupported worker claims and pending operations cannot advance maintenance success', async () => {
  const input = await fixture();
  const receipt = path.join(input.stateRoot, 'maintenance.json');
  const unsupported = JSON.stringify({ lastFullReconcileAt: new Date().toISOString(), model: 'gpt-6-luna', verified: true });
  await writeFile(receipt, unsupported);
  assert.equal((await verifiedMaintenanceStatus(input)).fullReconcileDue, true);
  await assert.rejects(inspectMaintenance({ ...input, verified: true }), /Caller-authored/);
  await mkdir(path.join(input.stateRoot, 'operations'));
  await writeFile(path.join(input.stateRoot, 'operations/pending.json'), '{}');
  const blocked = await inspectMaintenance(input);
  assert.equal(blocked.status, 'blocked');
  assert.equal(await readFile(receipt, 'utf8'), unsupported);
});

test('dry-run and divergent baseline views leave maintenance state unchanged', async () => {
  const input = await fixture();
  const result = await inspectMaintenance({ ...input, dryRun: true });
  assert.equal(result.status, 'preview');
  await assert.rejects(stat(path.join(input.stateRoot, 'maintenance-inspection.json')), { code: 'ENOENT' });
  await writeFile(path.join(input.stateRoot, 'reconciliation.json'), JSON.stringify({ records: {
    '019a1234-5678-7abc-8def-000000000001': { canonical: { state: 'completed' }, views: {} }
  } }));
  const blocked = await inspectMaintenance(input);
  assert.equal(blocked.status, 'blocked');
  assert.ok(blocked.diagnostics.some(issue => issue.code === 'canonical-needs-reconciliation'));
  await writeFile(path.join(input.stateRoot, 'reconciliation.json'), JSON.stringify({ records: {
    '019a1234-5678-7abc-8def-000000000001': { canonical: [], views: {} }
  } }));
  assert.ok((await inspectMaintenance(input)).diagnostics.some(issue => issue.code === 'invalid-baseline-record'));
});

test('attachment deletion and linked heading changes invalidate inspection freshness', async () => {
  const input = await fixture();
  const attachment = path.join(input.projectsRoot, 'alpha/inputs/evidence.pdf');
  const heading = path.join(input.projectsRoot, 'alpha/inputs/context.md');
  await mkdir(path.dirname(attachment));
  await writeFile(attachment, 'attachment');
  await writeFile(heading, '# Evidence\n');
  await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\n[Evidence](inputs/evidence.pdf)\n[Context](inputs/context.md#evidence)\n');
  const inspected = await inspectMaintenance(input);
  assert.equal(inspected.status, 'inspected');
  assert.equal(inspected.value.navigationTargets.length, 2);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
  await unlink(attachment);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await writeFile(attachment, 'attachment');
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
  await writeFile(heading, '# Different heading\n');
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  assert.equal((await verifiedMaintenanceStatus(input)).fullReconcileDue, true);
});

test('missing or unsafe navigation observations cannot establish inspection freshness', async () => {
  const input = await fixture();
  const inspected = await inspectMaintenance(input);
  const receipt = path.join(input.stateRoot, 'maintenance-inspection.json');
  const { navigationTargets, ...missingTargets } = inspected.value;
  await writeFile(receipt, JSON.stringify(missingTargets));
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await writeFile(receipt, JSON.stringify({ ...inspected.value, navigationTargets: [{ path: path.join(input.stateRoot, 'decision-log.jsonl'), sha256: null }] }));
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await writeFile(receipt, JSON.stringify({ ...inspected.value, navigationTargets: [{ path: input.project, sha256: 'invalid' }] }));
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
});
