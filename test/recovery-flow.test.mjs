import test from 'node:test';
import assert from 'node:assert/strict';
import fs, { readFile, writeFile, mkdir, unlink, access } from 'node:fs/promises';
import { syncBuiltinESMExports } from 'node:module';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { tmpdir } from 'node:os';
import { seedPlanningFixture, inspectPlanningFixture, planningHash } from '../evals/planning-fixture.mjs';
import { appendDecision, queryDecisions } from '../lib/log/decision-log.mjs';
import { invalidateInventory } from '../lib/inventory/inventory.mjs';
import { completeOperation, verifyOperation } from '../lib/operations/verification.mjs';

const input = fixture => ({vaultRoot:fixture.vaultRoot,stateRoot:fixture.stateRoot,homeRoot:fixture.vaultRoot,now:fixture.now,operationPath:fixture.checkpointPath});

// File tools author only Markdown. Production verifies and completes all owned state.
async function resumeFixture(fixture) {
  const observed = await inspectPlanningFixture(fixture);
  if (observed.recovery.status === 'conflict' || observed.unexpectedFiles.length || observed.productionVerification?.status === 'conflict') return {status:'conflict'};
  if (observed.checkpointRemoved) return {status:'complete'};
  for (const effect of observed.recovery.pending) {
    if (effect.key === 'destinationMember') await writeFile(fixture.destination,fixture.destinationAfter);
    if (effect.key === 'sourceMember') await writeFile(fixture.source,fixture.sourceAfter);
    if (['destinationMember','sourceMember'].includes(effect.key)) await invalidateInventory(fixture);
    if (effect.key === 'logRecorded') await appendDecision({projectsRoot:fixture.projectsRoot,entry:fixture.operation.event});
  }
  const completed = await completeOperation(input(fixture));
  if (completed.status !== 'completed') return completed;
  assert.equal((await inspectPlanningFixture(fixture)).verified,true);
  return {status:'complete'};
}

for (const stage of [0,1,2,3,4]) test(`future move interrupted after stage ${stage} resumes with one date and one decision`,async () => {
  const fixture = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),stage);
  const before = await inspectPlanningFixture(fixture);
  assert.equal(before.completion,undefined);
  assert.equal(before.productionVerification.persistedStatus,stage >= 3 ? 'verified' : 'pending');
  assert.equal(before.productionVerification.status,stage === 4 ? 'verified' : 'pending');
  if (stage === 3) assert.equal(before.productionVerification.ownedState.pending.length,3);
  if (stage === 4) assert.equal(before.productionVerification.ownedState.pending.length,0);
  assert.equal((await resumeFixture(fixture)).status,'complete');
  const after = await inspectPlanningFixture(fixture);
  assert.equal(after.verified,true);
  assert.equal(after.otherPreserved,true);
  assert.equal(after.prosePreserved,true);
  assert.equal(after.planIdentityPreserved,true);
  assert.equal(after.rolloverPreserved,true);
  assert.equal(after.historyPreserved,true);
  assert.equal(after.canonicalPreserved,true);
  assert.equal(after.checkpointIntentPreserved,true);
  await assert.rejects(access(fixture.checkpointPath),{code:'ENOENT'});
  assert.equal(after.checkpointRemoved,true);
  assert.equal((await resumeFixture(fixture)).status,'complete');
  assert.equal((await queryDecisions({projectsRoot:fixture.projectsRoot})).total,1);
  assert.equal((await appendDecision({projectsRoot:fixture.projectsRoot,entry:fixture.operation.event})).duplicate,true);
});

test('recovery preserves unexpected prose and baseline edits without false completion',async () => {
  for (const changed of ['source','baselinePath']) {
    const fixture = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),1);
    const filename = fixture[changed];
    const original = await readFile(filename,'utf8');
    const modified = changed === 'source' ? original+'\nAn independent edit to preserve.\n' : JSON.stringify({schemaVersion:1,unexpected:'conflicting baseline'});
    await writeFile(filename,modified);
    assert.equal((await resumeFixture(fixture)).status,'conflict');
    assert.equal(await readFile(filename,'utf8'),modified);
    assert.equal((await inspectPlanningFixture(fixture)).completion,undefined);
    assert.equal((await queryDecisions({projectsRoot:fixture.projectsRoot})).total,0);
  }
});

test('conflicting recorded decisions remain visible even when their record_ids differ',async () => {
 for (const change of [{after:{date:'different'}},{record_ids:[]}]) {
  const fixture = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),2);
  const directory = path.join(fixture.projectsRoot,'.daily-tasks');
  await mkdir(directory,{recursive:true});
  // A conflicting prior event is an immediate hard failure, not a slow lock timeout.
  await appendDecision({projectsRoot:fixture.projectsRoot,entry:{...fixture.operation.event,...change}});
  assert.equal((await resumeFixture(fixture)).status,'conflict');
  const pending = await inspectPlanningFixture(fixture);
  assert.equal(pending.completion,undefined);
  assert.equal(pending.actual.baselineHash,planningHash(fixture.baselineBefore));
 }
});

test('recovery oracle rejects altered canonical files, checkpoint binding and invalid completion',async () => {
  for (const changed of ['canonical','binding','completion']) {
    const fixture = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),4);
    if (changed === 'canonical') {
      const filename = Object.keys(fixture.canonicalHashes).find(filename => filename.endsWith('other-task.md'));
      await writeFile(filename,(await readFile(filename,'utf8')).replace('title: "Other task"','title: "Unexpected title"'));
    } else {
      const checkpoint = JSON.parse(await readFile(fixture.checkpointPath,'utf8'));
      if (changed === 'binding') checkpoint.contextBinding = '0'.repeat(64);
      else checkpoint.completedAt = 'invalid';
      await writeFile(fixture.checkpointPath,JSON.stringify(checkpoint));
    }
    assert.equal((await inspectPlanningFixture(fixture)).verified,false);
  }
});

test('oracle accepts removal of a completed checkpoint and rejects absence during pending effects',async () => {
  const pending = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),1);
  await unlink(pending.checkpointPath);
  assert.equal((await inspectPlanningFixture(pending)).verified,false);
  const complete = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),4);
  await resumeFixture(complete);
  await assert.rejects(access(complete.checkpointPath),{code:'ENOENT'});
  const verified = await inspectPlanningFixture(complete);
  assert.equal(verified.verified,true);
  assert.equal(verified.checkpointRemoved,true);
});


test('selection completion preserves removal history, receipt fields and unrelated baselines',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  const before = await verifyOperation(input(f));
  assert.equal(before.status,'pending');
  assert.equal(before.persistedStatus,'verified');
  assert.ok(before.pending.every(item => item.kind === 'owned-state'));
  assert.equal((await completeOperation({...input(f),dryRun:true})).status,'preview');
  assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
  assert.equal((await completeOperation(input(f))).status,'completed');
  for (const [filename,expected] of [[f.sourceRolloverPath,f.sourceRolloverAfter],[f.destinationRolloverPath,f.destinationRollover]]) {
    const state = JSON.parse(await readFile(filename,'utf8'));
    assert.deepEqual(state,expected);
    assert.ok(state.removedIds.includes(f.ids.unrelatedRemoval));
    assert.equal(state.completedAt,f.now);
  }
  assert.deepEqual(JSON.parse(await readFile(f.baselinePath,'utf8')).records[f.ids.other],JSON.parse(f.baselineBefore).records[f.ids.other]);
});

test('all owned states and baseline preflight before any write; unexpected bytes conflict',async () => {
  for (const key of ['sourceRolloverPath','destinationRolloverPath','baselinePath']) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
    const original = await Promise.all([f.sourceRolloverPath,f.destinationRolloverPath,f.baselinePath].map(filename => readFile(filename,'utf8')));
    // Even a semantically equal but byte-different before snapshot is an edit.
    const changed = original[['sourceRolloverPath','destinationRolloverPath','baselinePath'].indexOf(key)]+' ';
    await writeFile(f[key],changed);
    for (const command of [verifyOperation,completeOperation]) {
      const result = await command(input(f));
      assert.equal(result.status,'conflict');
      assert.equal(result.persistedStatus,'verified');
      assert.ok(result.ownedState.conflicts.some(conflict => conflict.path === f[key]));
    }
    for (const [i,k] of ['sourceRolloverPath','destinationRolloverPath','baselinePath'].entries()) assert.equal(await readFile(f[k],'utf8'),k === key ? changed : original[i]);
    await access(f.checkpointPath);
  }
});

test('partial production writes retain checkpoint and resume without reapplying prior state',async () => {
  for (const failurePath of ['destinationRolloverPath','baselinePath']) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
    const rename = fs.rename;
    fs.rename = async (from,to) => { if (to === f[failurePath]) throw new Error('Injected atomic-write failure'); return rename(from,to); };
    syncBuiltinESMExports();
    try { await assert.rejects(completeOperation(input(f)),/Injected/); }
    finally { fs.rename = rename; syncBuiltinESMExports(); }
    await access(f.checkpointPath);
    const prior = await readFile(f.sourceRolloverPath,'utf8');
    assert.deepEqual(JSON.parse(prior),f.sourceRolloverAfter);
    const verified = await verifyOperation(input(f));
    assert.equal(verified.status,'pending');
    assert.equal(verified.persistedStatus,'verified');
    assert.equal(verified.ownedState.pending.length,failurePath === 'destinationRolloverPath' ? 2 : 1);
    assert.equal((await completeOperation(input(f))).status,'completed');
    assert.equal(await readFile(f.sourceRolloverPath,'utf8'),prior);
    assert.equal((await inspectPlanningFixture(f)).verified,true);
  }
});

test('protected canonical and historical sources block completion without state writes',async () => {
  for (const key of ['historyPath','canonical']) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
    const filename = key === 'canonical' ? Object.keys(f.canonicalHashes).find(name => name.endsWith('recovery-task.md')) : f[key];
    await writeFile(filename,(await readFile(filename,'utf8'))+'\nIndependent protected-file edit.\n');
    assert.equal((await verifyOperation(input(f))).status,'conflict');
    assert.equal((await completeOperation(input(f))).status,'conflict');
    assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
    assert.deepEqual(JSON.parse(await readFile(f.sourceRolloverPath,'utf8')),f.sourceRolloverBefore);
    await access(f.checkpointPath);
  }
});

test('selection intent rejects altered direction, event, identity, before evidence and arbitrary state replacements',async () => {
  const cases = [
    f => { f.operation.selectionState.direction = 'add'; },
    f => { f.operation.selectionState.source = null; },
    f => { f.operation.selectionState = null; },
    f => { f.operation.selectionState.taskIds = [f.ids.other]; },
    f => { f.operation.event.after.date = f.today; },
    f => { f.operation.event.id = 'invalid'; },
    f => { f.operation.selectionState.source.planId = f.ids.destination; },
    f => { f.operation.selectionState.source.beforeMarkdown += '\nTampered before'; },
    f => { f.operation.selectionState.destination.stateBeforeText += ' '; },
    f => { f.operation.selectionState.source.stateBeforeHash = null; },
    f => { f.operation.selectionState.source.planPath = f.historyPath; },
    f => { f.operation.selectionState.source.after = f.sourceRolloverAfter; },
    f => { f.operation.changes = [{key:'ignored'}]; },
    f => { delete f.operation.baseline; },
    f => { f.operation.baseline.value.records[f.ids.task].views[f.source] = JSON.parse(f.baselineBefore).records[f.ids.task].views[f.source]; },
  ];
  for (const change of cases) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
    change(f); await writeFile(f.checkpointPath,JSON.stringify(f.operation));
    await assert.rejects(completeOperation(input(f)),/Selection|selection|Unsupported|Legacy/);
    assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
    await access(f.checkpointPath);
  }
});

test('a declared after hash cannot excuse wrong membership or creation identity',async () => {
  for (const change of ['duplicate','unrelated','created']) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
    const markdown = change === 'duplicate' ? f.destinationAfter + `\n- [ ] Copy <!-- ref: ${f.ids.task} -->\n` :
      change === 'unrelated' ? f.sourceAfter.replace(f.ids.other,f.ids.unrelatedRemoval) : f.sourceAfter.replace(`created_at: "${f.now}"`,'created_at: "2026-01-01T12:00:00Z"');
    const filename = change === 'duplicate' ? f.destination : f.source;
    await writeFile(filename,markdown);
    f.operation.files.find(file => file.path === filename).after = planningHash(markdown);
    await writeFile(f.checkpointPath,JSON.stringify(f.operation));
    await assert.rejects(completeOperation(input(f)),/membership|creation time/);
    await access(f.checkpointPath);
  }
});


test('add and remove intents derive only their dated state; absence creates no rollover receipt',async () => {
  for (const direction of ['add','remove']) for (const absent of [false,true]) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),direction === 'add' ? 0 : 2);
    const adding = direction === 'add', plan = adding ? f.operation.selectionState.destination : f.operation.selectionState.source;
    const statePath = adding ? f.destinationRolloverPath : f.sourceRolloverPath;
    if (adding) await writeFile(f.destination,f.destinationAfter);
    f.operation.selectionState.direction = direction;
    delete f.operation.selectionState[adding ? 'source' : 'destination'];
    f.operation.files = f.operation.files.filter(file => file.path === plan.planPath);
    f.operation.event.action = `selection-${direction}`;
    f.operation.event.before.date = adding ? null : f.today;
    f.operation.event.after.date = adding ? f.nextDay : null;
    if (adding) f.operation.baseline.value.records[f.ids.task].views[f.source] = JSON.parse(f.baselineBefore).records[f.ids.task].views[f.source];
    else delete f.operation.baseline.value.records[f.ids.task].views[f.destination];
    if (absent) { await unlink(statePath); plan.stateBeforeHash = null; plan.stateBeforeText = null; }
    await writeFile(f.checkpointPath,JSON.stringify(f.operation));
    await appendDecision({projectsRoot:f.projectsRoot,entry:f.operation.event});
    const unaffected = adding ? f.sourceRolloverPath : f.destinationRolloverPath;
    const unaffectedBefore = await readFile(unaffected,'utf8');
    assert.equal((await completeOperation(input(f))).status,'completed');
    const state = JSON.parse(await readFile(statePath,'utf8'));
    assert.deepEqual(state.removedIds,adding ? absent ? [] : [f.ids.unrelatedRemoval] : absent ? [f.ids.task] : [f.ids.unrelatedRemoval,f.ids.task]);
    if (absent) assert.deepEqual(state,{schemaVersion:1,date:plan.date,planId:plan.planId,removedIds:adding ? [] : [f.ids.task]});
    else assert.equal(state.operationId,adding ? f.ids.destinationRollover : f.ids.rollover);
    assert.equal(await readFile(unaffected,'utf8'),unaffectedBefore);
  }
});

test('missing move state initializes both dates without inventing rollover completion',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  for (const [key,filename] of [['source',f.sourceRolloverPath],['destination',f.destinationRolloverPath]]) {
    await unlink(filename);
    Object.assign(f.operation.selectionState[key],{stateBeforeHash:null,stateBeforeText:null});
  }
  await writeFile(f.checkpointPath,JSON.stringify(f.operation));
  assert.equal((await completeOperation(input(f))).status,'completed');
  assert.deepEqual(JSON.parse(await readFile(f.sourceRolloverPath,'utf8')),{schemaVersion:1,date:f.today,planId:f.ids.source,removedIds:[f.ids.task]});
  assert.deepEqual(JSON.parse(await readFile(f.destinationRolloverPath,'utf8')),{schemaVersion:1,date:f.nextDay,planId:f.ids.destination,removedIds:[]});
});

test('selection completion refuses missing canonical protection and unsupported baseline proposals',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  f.operation.protectedFiles = f.operation.protectedFiles.filter(file => !file.path.endsWith('recovery-task.md'));
  await writeFile(f.checkpointPath,JSON.stringify(f.operation));
  assert.equal((await completeOperation(input(f))).status,'conflict');
  assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
  const g = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  delete g.operation.baseline.value.records[g.ids.other];
  await writeFile(g.checkpointPath,JSON.stringify(g.operation));
  await assert.rejects(completeOperation(input(g)),/cannot retire records/);
  assert.deepEqual(JSON.parse(await readFile(g.sourceRolloverPath,'utf8')),g.sourceRolloverBefore);
  assert.equal(await readFile(g.baselinePath,'utf8'),g.baselineBefore);
});

test('optimistic state race preserves the edit and makes partial work safely inspectable',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  const write = fs.writeFile, changed = JSON.stringify({...f.destinationRolloverBefore,removedIds:[]});
  let injected = false;
  fs.writeFile = async (filename,...args) => {
    const result = await write(filename,...args);
    if (!injected && filename.startsWith(f.destinationRolloverPath+'.') && filename.endsWith('.tmp')) {
      injected = true; await write(f.destinationRolloverPath,changed);
    }
    return result;
  };
  syncBuiltinESMExports();
  try { await assert.rejects(completeOperation(input(f)),/State changed before completion/); }
  finally { fs.writeFile = write; syncBuiltinESMExports(); }
  assert.equal(await readFile(f.destinationRolloverPath,'utf8'),changed);
  assert.deepEqual(JSON.parse(await readFile(f.sourceRolloverPath,'utf8')),f.sourceRolloverAfter);
  assert.equal((await verifyOperation(input(f))).status,'conflict');
  assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
  await access(f.checkpointPath);
});


test('packaged CLI completes stage3 and resumes already-applied stage4 from an unrelated cwd',async () => {
  const execute = promisify(execFile);
  for (const stage of [3,4]) for (const entry of ['artifacts/portable/bin/daily-tasks.mjs','artifacts/cowork/scripts/daily-tasks.mjs']) {
    const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),stage);
    const inputPath = path.join(f.vaultRoot,'completion-input.json');
    await writeFile(inputPath,JSON.stringify(input(f)));
    const result = await execute(process.execPath,[path.resolve(entry),'operation-complete','--input',inputPath],{cwd:tmpdir()});
    assert.equal(JSON.parse(result.stdout).status,'completed');
    assert.equal((await inspectPlanningFixture(f)).verified,true);
    await assert.rejects(access(f.checkpointPath),{code:'ENOENT'});
  }
});

test('multiple explicit task IDs union source removals and clear only those IDs at destination',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),2);
  const otherRow = f.sourceAfter.match(/^- \[ \].*Other task.*\n/m)[0];
  const sourceAfter = f.sourceAfter.replace(otherRow,''), destinationAfter = f.destinationAfter.replace('## Notes',otherRow+'\n## Notes');
  await writeFile(f.source,sourceAfter); await writeFile(f.destination,destinationAfter);
  f.operation.selectionState.taskIds.push(f.ids.other);
  f.operation.event.record_ids.push(f.ids.other);
  for (const [filename,markdown] of [[f.source,sourceAfter],[f.destination,destinationAfter]]) f.operation.files.find(file => file.path === filename).after = planningHash(markdown);
  for (const id of [f.ids.task,f.ids.other]) f.operation.baseline.value.records[id].views = {
    [f.source]:{selected:false,hash:planningHash(sourceAfter)},[f.destination]:{selected:true,hash:planningHash(destinationAfter)}
  };
  // An already-listed source removal remains once; only remaining intended IDs are appended.
  const sourceBefore = {...f.sourceRolloverBefore,removedIds:[f.ids.unrelatedRemoval,f.ids.task]};
  await writeFile(f.sourceRolloverPath,JSON.stringify(sourceBefore));
  Object.assign(f.operation.selectionState.source,{stateBeforeHash:planningHash(JSON.stringify(sourceBefore)),stateBeforeText:JSON.stringify(sourceBefore)});
  await writeFile(f.checkpointPath,JSON.stringify(f.operation));
  await appendDecision({projectsRoot:f.projectsRoot,entry:f.operation.event});
  assert.equal((await completeOperation(input(f))).status,'completed');
  assert.deepEqual(JSON.parse(await readFile(f.sourceRolloverPath,'utf8')).removedIds,[f.ids.unrelatedRemoval,f.ids.task,f.ids.other]);
  assert.deepEqual(JSON.parse(await readFile(f.destinationRolloverPath,'utf8')).removedIds,[f.ids.unrelatedRemoval]);
});


test('relabeling legacy changes as schema-v2 cannot silently complete unverified owned work',async () => {
  const f = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),3);
  delete f.operation.selectionState;
  f.operation.changes = [{key:'legacy-state',before:{present:true,value:false},after:{present:true,value:true}}];
  await writeFile(f.checkpointPath,JSON.stringify(f.operation));
  for (const command of [verifyOperation,completeOperation]) await assert.rejects(command(input(f)),/Legacy changes/);
  assert.equal(await readFile(f.baselinePath,'utf8'),f.baselineBefore);
  await access(f.checkpointPath);
});
