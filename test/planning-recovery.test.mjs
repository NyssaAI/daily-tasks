import test from 'node:test';
import assert from 'node:assert/strict';
import fs, { mkdir, mkdtemp, realpath, readFile, writeFile } from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { uuid7 } from '../lib/identity/identity.mjs';
import { resolveContext } from '../lib/profile/context.mjs';
import { preparePlanning, savePlanningState } from '../lib/planning/session.mjs';
import { planSelection } from '../lib/planning/review.mjs';
import { inspectMaintenance } from '../lib/planning/maintenance.mjs';
import { planningScreen } from './fixtures/planning-screen.mjs';
import { seedPlanningFixture } from '../evals/planning-fixture.mjs';

const hash = value => createHash('sha256').update(value).digest('hex');
async function fixture() {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/planning-recovery-')));
  const input = {vaultRoot:root,homeRoot:root,now:'2026-10-13T14:00:00Z',dryRun:true};
  const state = path.join(root,'.nyssa-ai/daily-tasks');
  for (const directory of [state,path.join(state,'operations'),path.join(root,'daily')]) await mkdir(directory,{recursive:true});
  await writeFile(path.join(state,'profile.json'),JSON.stringify({schema_version:2,user:{name:'Owner',email:'owner@example.test'},timezone:'UTC',projectsRoot:'./projects',dailyPlansRelative:'daily'}));
  const records = {};
  const doc = (id,type,extra,body='') => `---\nid: ${id}\ntype: ${type}\ntitle: Example\nowner: owner@example.test\n${type}-state: not-started\ncreated_at: 2026-10-13T14:00:00Z\nupdated_at: 2026-10-13T14:00:00Z\n${extra}---\n${body}`;
  for (const name of ['alpha','beta']) {
    const projectId = uuid7(), milestoneId = uuid7(), taskId = uuid7();
    const directory = path.join(root,'projects',name);
    await mkdir(directory,{recursive:true});
    const project = path.join(directory,'project-index.md'), milestone = path.join(directory,'milestone.md'), task = path.join(directory,'task.md');
    await writeFile(project,doc(projectId,'project','',`| Milestone | Task |\n| --- | --- |\n| [ ] [[milestone\\|Example]] <!-- ref: ${milestoneId} --> | |\n| | [ ] [[task\\|Example]] <!-- ref: ${taskId} --> |\n`));
    await writeFile(milestone,doc(milestoneId,'milestone',`project_id: ${projectId}\n`));
    await writeFile(task,doc(taskId,'task',`project_id: ${projectId}\nmilestone_id: ${milestoneId}\n`));
    records[name] = {projectId,milestoneId,taskId,project,milestone,task};
  }
  const current = path.join(root,'daily/2026.10.13-daily-plan.md');
  await writeFile(current,`---\nid: ${uuid7()}\ntype: daily-plan\n---\n`);
  const context = await resolveContext(input);
  async function checkpoint(filename,extra={}) {
    const operationId = uuid7(), operationPath = path.join(state,'operations',`${operationId}.json`);
    let before = null; try { before = hash(await readFile(filename)); } catch (error) { if (error.code !== 'ENOENT') throw error; }
    const operation = {schemaVersion:2,operation_id:operationId,contextBinding:context.planningBinding,
      event:{id:uuid7(),operation_id:operationId,action:'update',record_ids:[]},
      files:[{path:filename,before,after:hash('different')}],...extra};
    await writeFile(operationPath,JSON.stringify(operation));
    return {operationPath,operation};
  }
  return {input,state,records,current,checkpoint};
}
const request = (f,p) => ({...f.input,dryRun:false,action:'save-review',expectedPlanHash:p.current.sha256,
  expectedPreviousHash:p.previous?.sha256 ?? null,expectedStateHash:p.state.review.sha256,
  expectedInventoryHash:p.inventoryHash,expectedReviewHash:p.reviewHash,reviewMarkdown:planningScreen(p)});

test('unrelated task recovery suspends that addition while an independent numbered review saves',async () => {
  const f = await fixture();
  const initial = await preparePlanning(f.input);
  await savePlanningState(request(f,initial));
  const pending = await f.checkpoint(f.records.beta.task);
  const checkpointBytes = await readFile(pending.operationPath,'utf8'), recordBytes = await readFile(f.records.beta.task,'utf8');
  const packet = await preparePlanning(f.input);
  assert.equal(packet.status,'prepared');
  assert.deepEqual(packet.review.available.map(row => row.id),[f.records.alpha.taskId]);
  assert.equal(packet.review.mapping[f.records.alpha.taskId],initial.review.mapping[f.records.alpha.taskId]);
  assert.ok(packet.review.diagnostics.some(issue => issue.code === 'pending-operation' && issue.recordId === f.records.beta.taskId));
  const selection = planSelection({...packet.context,inventory:packet.inventory,recovery:packet.recovery,action:'add',
    today:packet.context.localDate,date:packet.context.localDate,taskIds:[f.records.alpha.taskId,f.records.beta.taskId]});
  assert.deepEqual(selection.effects.map(effect => effect.id),[f.records.alpha.taskId]);
  assert.deepEqual(selection.conflicts,[{id:f.records.beta.taskId,reason:'pending-operation'}]);
  assert.equal((await savePlanningState(request(f,packet))).status,'saved');
  assert.equal((await inspectMaintenance({...f.input,dryRun:true})).status,'blocked');
  assert.equal(await readFile(pending.operationPath,'utf8'),checkpointBytes);
  assert.equal(await readFile(f.records.beta.task,'utf8'),recordBytes);
});

test('affected selections remain visible and suspended; project ordering suspends additions',async () => {
  const f = await fixture();
  await writeFile(f.current,(await readFile(f.current,'utf8'))+`\n- [ ] [[../projects/beta/task|Example]] <!-- ref: ${f.records.beta.taskId} -->\n`);
  await f.checkpoint(f.records.beta.milestone);
  const packet = await preparePlanning(f.input);
  assert.equal(packet.status,'prepared');
  assert.equal(packet.review.selected.find(row => row.id === f.records.beta.taskId).unresolved,true);
  assert.equal(packet.review.selected.find(row => row.id === f.records.beta.taskId).suspended,true);
  assert.deepEqual(packet.review.available.map(row => row.id),[f.records.alpha.taskId]);
  await assert.rejects(savePlanningState({...request(f,packet),action:'complete-rollover',expectedStateHash:packet.state.rollover.sha256}),/Selected work.*reconciliation/);
});

test('typed selection state is classified without changing checkpoints, dated history or canonical records',async () => {
  const fixtureRoot = path.resolve('.temp/planning-recovery-typed');
  const f = await seedPlanningFixture(fixtureRoot,0,'2026-10-13T14:00:00Z');
  const unchangedPaths = [f.checkpointPath,f.baselinePath,f.sourceRolloverPath,f.destinationRolloverPath,...Object.keys(f.canonicalHashes)];
  const before = await Promise.all(unchangedPaths.map(filename => readFile(filename,'utf8')));
  const affected = await preparePlanning({vaultRoot:f.vaultRoot,homeRoot:f.vaultRoot,stateRoot:f.stateRoot,now:f.now,dryRun:true});
  assert.equal(affected.status,'recovery-required');
  assert.deepEqual(affected.recovery.operations[0].statePaths,[f.sourceRolloverPath,f.destinationRolloverPath].sort());
  const earlier = path.join(f.dailyPlansRoot,'2026.10.11-daily-plan.md');
  await writeFile(earlier,`---\nid: ${uuid7()}\ntype: daily-plan\n---\n`);
  const independent = await preparePlanning({vaultRoot:f.vaultRoot,homeRoot:f.vaultRoot,stateRoot:f.stateRoot,now:'2026-10-11T14:00:00Z',dryRun:true});
  assert.equal(independent.status,'prepared');
  assert.deepEqual(await Promise.all(unchangedPaths.map(filename => readFile(filename,'utf8'))),before);
  f.operation.selectionState.destination.stateBeforeHash = 'invalid';
  await writeFile(f.checkpointPath,JSON.stringify(f.operation));
  const invalid = await preparePlanning({vaultRoot:f.vaultRoot,homeRoot:f.vaultRoot,stateRoot:f.stateRoot,now:'2026-10-11T14:00:00Z',dryRun:true});
  assert.equal(invalid.status,'recovery-required');
  assert.equal(invalid.recovery.operations[0].status,'unknown');
});

test('a validated foreign binding is suspended but disjoint effects permit independent review',async () => {
  const f = await fixture();
  await f.checkpoint(f.records.beta.task,{contextBinding:'0'.repeat(64)});
  const packet = await preparePlanning(f.input);
  assert.equal(packet.status,'prepared');
  assert.equal(packet.recovery.operations[0].foreign,true);
  assert.equal(packet.recovery.operations[0].status,'scoped');
  assert.deepEqual(packet.review.available.map(row => row.id),[f.records.alpha.taskId]);
});

test('checkpoint introduced during a save is rejected by the final optimistic recheck',async () => {
  const f = await fixture(), packet = await preparePlanning(f.input);
  const original = fs.writeFile;
  let inserted = false;
  fs.writeFile = async (filename,...args) => {
    const result = await original(filename,...args);
    if (!inserted && filename.startsWith(packet.state.review.path) && filename.endsWith('.tmp')) {
      inserted = true;
      await f.checkpoint(f.current);
    }
    return result;
  };
  syncBuiltinESMExports();
  try { await assert.rejects(savePlanningState(request(f,packet)),/checkpoint evidence changed/); }
  finally { fs.writeFile = original; syncBuiltinESMExports(); }
  assert.equal(inserted,true);
  await assert.rejects(readFile(packet.state.review.path),{code:'ENOENT'});
});

test('review evidence ignores an inventory refresh timestamp while preserving source checks',async () => {
  const f = await fixture(), packet = await preparePlanning(f.input);
  const requestLater = {...request(f,packet),now:'2026-10-13T14:01:00Z'};
  assert.equal((await savePlanningState(requestLater)).status,'saved');
});

test('current and rollover-source plans block saves while a disjoint future plan does not',async () => {
  for (const date of ['2026.10.13','2026.10.12','2026.10.15']) {
    const f = await fixture(), target = path.join(f.input.vaultRoot,'daily',`${date}-daily-plan.md`);
    if (date !== '2026.10.13') await writeFile(target,`---\nid: ${uuid7()}\ntype: daily-plan\n---\n`);
    await f.checkpoint(target);
    const packet = await preparePlanning(f.input);
    assert.equal(packet.status,date === '2026.10.15' ? 'prepared' : 'recovery-required');
    if (date !== '2026.10.15') await assert.rejects(savePlanningState(request(f,packet)),/recovery|recovered/i);
  }
});

test('unknown, malformed and unsafe checkpoints fail closed; legacy completion receipts are ignored',async () => {
  for (const kind of ['malformed','unsafe','unknown','foreign','completed']) {
    const f = await fixture(), pending = await f.checkpoint(f.records.beta.task);
    if (kind === 'malformed') await writeFile(pending.operationPath,'{');
    else {
      if (kind === 'unsafe') pending.operation.files[0].path = path.join(f.state,'review/2026.10.13.json');
      if (kind === 'unknown') pending.operation.ownedState = {path:'unknown'};
      if (kind === 'foreign') pending.operation.contextBinding = 'other-vault';
      if (kind === 'completed') pending.operation.status = 'completed';
      await writeFile(pending.operationPath,JSON.stringify(pending.operation));
    }
    assert.equal((await preparePlanning(f.input)).status,kind === 'completed' ? 'prepared' : 'recovery-required',kind);
  }
});

test('protected dependencies suspend their record and checkpoint changes invalidate prior review evidence',async () => {
  const f = await fixture(), initial = await preparePlanning(f.input);
  const pending = await f.checkpoint(path.join(f.input.vaultRoot,'daily/2026.10.15-daily-plan.md'),
    {protectedFiles:[{path:f.records.beta.task,sha256:hash(await readFile(f.records.beta.task))}]});
  await assert.rejects(savePlanningState(request(f,initial)),/changed|prepare/i);
  const prepared = await preparePlanning(f.input);
  assert.equal(prepared.status,'prepared');
  assert.equal(prepared.review.pageCount,1);
  pending.operation.files[0].after = hash('changed checkpoint');
  await writeFile(pending.operationPath,JSON.stringify(pending.operation));
  await assert.rejects(savePlanningState(request(f,prepared)),/changed|prepare/i);
  const refreshed = await preparePlanning(f.input);
  assert.equal((await savePlanningState(request(f,refreshed))).status,'saved');
});
