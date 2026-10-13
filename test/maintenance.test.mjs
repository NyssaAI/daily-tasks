import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, stat, unlink, rm, symlink } from 'node:fs/promises';
import path from 'node:path';
import { inspectMaintenance, verifiedMaintenanceStatus } from '../lib/planning/maintenance.mjs';
import { preparePlanning, savePlanningState } from '../lib/planning/session.mjs';

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
  assert.equal((await verifiedMaintenanceStatus(input)).fullReconcileDue, null);
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
  const status = await verifiedMaintenanceStatus(input);
  assert.equal(status.fullReconcileDue, null);
  assert.equal(status.workerEvidence.status, 'unsupported');
  for (const key of ['verified', 'executionEvidence', 'worker', 'model', 'lastFullReconcileAt', 'receipt']) {
    await assert.rejects(inspectMaintenance({ ...input, [key]: unsupported }), /Caller-authored/);
  }
  await mkdir(path.join(input.stateRoot, 'operations'));
  const completed = '019a1234-5678-7abc-8def-000000000009';
  await writeFile(path.join(input.stateRoot, `operations/${completed}.json`), JSON.stringify({ operation_id: completed, status: 'completed', files: [] }));
  assert.equal((await inspectMaintenance(input)).status, 'inspected');
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
  assert.equal((await verifiedMaintenanceStatus(input)).fullReconcileDue, null);
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

test('unsupported worker capability is explicit for missing and invalid inspection receipts', async () => {
  const input = await fixture();
  const expected = { status: 'unsupported', reason: 'trusted-worker-adapter-unavailable' };
  const setup = await verifiedMaintenanceStatus({ vaultRoot: input.vaultRoot, homeRoot: input.vaultRoot,
    configurationSources: { schemaVersion: 1, user: { profilePath: null }, project: { profilePath: null } } });
  assert.deepEqual(setup.workerEvidence, expected);
  assert.equal(setup.fullReconcileDue, null);
  assert.equal(setup.inspectionDue, true);
  assert.equal(setup.reason, 'setup-required');
  const missing = await verifiedMaintenanceStatus(input);
  assert.deepEqual(missing.workerEvidence, expected);
  assert.equal(missing.fullReconcileDue, null);
  assert.equal(missing.inspectionDue, true);
  assert.deepEqual(missing.alwaysCheck, ['current-plan-edits', 'previous-plan-edits', 'applicable-pending-operations']);
  await writeFile(path.join(input.stateRoot, 'maintenance-inspection.json'), '{broken');
  const invalid = await verifiedMaintenanceStatus(input);
  assert.deepEqual(invalid.workerEvidence, expected);
  assert.equal(invalid.fullReconcileDue, null);
  assert.equal(invalid.inspectionDue, true);
  assert.equal(invalid.reason, 'invalid-maintenance-receipt');
});

test('direct CLI checks distinguish fresh and expired inspection without claiming worker completion', async () => {
  const input = await fixture();
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  const inspected = await inspectMaintenance(input);
  assert.equal(inspected.status, 'inspected');
  assert.equal(inspected.successAdvanced, false);
  const completed = Date.parse(inspected.value.completedAt);
  for (const [age, due] of [[0, false], [14400 * 1000 - 1, false], [14400 * 1000, true]]) {
    const status = await verifiedMaintenanceStatus({ ...input, now: new Date(completed + age).toISOString() });
    assert.equal(status.inspectionDue, due);
    assert.equal(status.inspectionReason, 'verified-cli-inspection');
    assert.equal(status.fullReconcileDue, null);
    assert.equal(status.workerEvidence.status, 'unsupported');
  }
  await assert.rejects(stat(path.join(input.stateRoot, 'maintenance.json')), { code: 'ENOENT' });
});

test('unsupported worker evidence and scoped failed direct checks do not block independent planning', async () => {
  const input = { ...await fixture(), now: '2026-10-13T12:00:00.000Z' };
  const initial = await preparePlanning(input);
  await writeFile(initial.current.path, `---\nid: 019a1234-5678-7abc-8def-000000000010\ntype: daily-plan\ntitle: Today\ncreated_at: ${input.now}\nupdated_at: ${input.now}\n---\n# Today\n`);
  await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\n[Missing attachment](inputs/missing.pdf)\n');
  const inspection = await inspectMaintenance(input);
  assert.equal(inspection.status, 'blocked');
  assert.ok(inspection.diagnostics.some(issue => issue.code === 'missing-link-target'));
  for (const action of ['save-review', 'complete-rollover']) {
    const packet = await preparePlanning(input);
    assert.equal(packet.status, 'prepared');
    assert.equal(packet.maintenance.workerEvidence.status, 'unsupported');
    assert.equal(packet.maintenance.fullReconcileDue, null);
    assert.equal(packet.maintenance.inspectionDue, true);
    const saved = await savePlanningState({ ...input, action,
      expectedPlanHash: packet.current.sha256, expectedPreviousHash: packet.previous?.sha256 ?? null,
      expectedStateHash: packet.state[action === 'save-review' ? 'review' : 'rollover'].sha256,
      expectedInventoryHash: packet.inventoryHash, expectedReviewHash: packet.reviewHash });
    assert.equal(saved.status, 'saved');
    assert.equal(JSON.parse(await readFile(saved.path, 'utf8')).planId, packet.current.id);
  }
  await assert.rejects(stat(path.join(input.stateRoot, 'maintenance-inspection.json')), { code: 'ENOENT' });
test('directory and file observations become stale after deletion or target kind changes', async t => {
  const input = await fixture();
  t.after(() => rm(input.vaultRoot, { recursive: true, force: true }));
  const directory = path.join(input.projectsRoot, 'alpha/inputs');
  const attachment = path.join(input.projectsRoot, 'alpha/proof.pdf');
  await mkdir(directory);
  await writeFile(attachment, 'proof');
  await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\n[Inputs](inputs/)\n[[inputs]]\n[Proof](proof.pdf)\n');
  const inspected = await inspectMaintenance(input);
  assert.equal(inspected.status, 'inspected');
  assert.deepEqual(inspected.value.navigationTargets, [
    { path: directory, kind: 'directory', sha256: null },
    { path: attachment, kind: 'file', sha256: null }
  ]);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
  await rm(directory, { recursive: true });
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await writeFile(directory, 'now a file');
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  await unlink(directory);
  await mkdir(directory);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
  await unlink(attachment);
  await mkdir(attachment);
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
});

test('distinct vault, projects and plans roots support plain and anchored vault resources', async t => {
  for (const syntax of ['markdown', 'wiki']) {
    await t.test(syntax, async t => {
      const input = await fixture();
      t.after(() => rm(input.vaultRoot, { recursive: true, force: true }));
      const resources = path.join(input.vaultRoot, '3-resources');
      const attachment = path.join(resources, 'proof.pdf');
      const heading = path.join(resources, 'context.md');
      await mkdir(resources);
      await writeFile(attachment, 'proof');
      await writeFile(heading, '# Evidence\n');
      const links = syntax === 'wiki' ? '[[3-resources/proof.pdf]]\n[[3-resources/context#Evidence]]\n[[3-resources/]]' :
        '[Proof](../../3-resources/proof.pdf)\n[Context](../../3-resources/context.md#evidence)\n[Resources](../../3-resources/)';
      await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\n' + links + '\n');
      const inspected = await inspectMaintenance(input);
      assert.equal(inspected.status, 'inspected');
      assert.equal(inspected.value.navigationTargets.length, 3);
      assert.equal(inspected.value.navigationTargets.find(target => target.path === heading).kind, 'file');
      assert.match(inspected.value.navigationTargets.find(target => target.path === heading).sha256, /^[a-f0-9]{64}$/);
      assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
      await unlink(attachment);
      assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
      await writeFile(attachment, 'proof');
      assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, false);
      await writeFile(heading, '# Changed\n');
      assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
      assert.ok((await inspectMaintenance(input)).diagnostics.some(issue => issue.code === 'missing-heading'));
    });
  }
});

test('vault target receipt validation rejects hidden, outside, symlink and malformed kinds', async t => {
  const input = await fixture();
  t.after(() => rm(input.vaultRoot, { recursive: true, force: true }));
  const resources = path.join(input.vaultRoot, '3-resources');
  await mkdir(resources);
  await writeFile(input.project, (await readFile(input.project, 'utf8')) + '\n[Resources](../../3-resources/)\n');
  const inspected = await inspectMaintenance(input);
  const receipt = path.join(input.stateRoot, 'maintenance-inspection.json');
  for (const target of [
    { path: input.stateRoot, kind: 'directory', sha256: null },
    { path: path.dirname(input.vaultRoot), kind: 'directory', sha256: null },
    { path: resources, kind: 'other', sha256: null },
    { path: resources, sha256: null },
    { path: resources, kind: 'directory', sha256: 'a'.repeat(64) }
  ]) {
    await writeFile(receipt, JSON.stringify({ ...inspected.value, navigationTargets: [target] }));
    assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
  }
  await writeFile(receipt, JSON.stringify(inspected.value));
  await rm(resources, { recursive: true });
  await symlink(input.projectsRoot, resources, 'junction');
  assert.equal((await verifiedMaintenanceStatus(input)).inspectionDue, true);
});
