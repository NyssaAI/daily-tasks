import test from 'node:test';
import assert from 'node:assert/strict';
import { readFile, writeFile, mkdir, unlink } from 'node:fs/promises';
import path from 'node:path';
import { seedPlanningFixture, inspectPlanningFixture, planningHash } from '../evals/planning-fixture.mjs';
import { appendDecision, queryDecisions } from '../lib/log/decision-log.mjs';
import { invalidateInventory } from '../lib/inventory/inventory.mjs';

// Test-only stand-in for the skill's file tools. No production Markdown writer.
async function resumeFixture(fixture) {
  const observed = await inspectPlanningFixture(fixture);
  if (observed.recovery.status === 'conflict' || observed.unexpectedFiles.length) return {status:'conflict'};
  for (const effect of observed.recovery.pending) {
    if (effect.key === 'destinationMember') await writeFile(fixture.destination,fixture.destinationAfter);
    if (effect.key === 'sourceMember') await writeFile(fixture.source,fixture.sourceAfter);
    if (['destinationMember','sourceMember'].includes(effect.key)) await invalidateInventory(fixture);
    if (effect.key === 'logRecorded') await appendDecision({projectsRoot:fixture.projectsRoot,entry:fixture.operation.event});
    if (effect.key === 'baselineHash') await writeFile(fixture.baselinePath,fixture.baselineAfter);
    if (effect.key === 'sourceRolloverHash') await writeFile(fixture.sourceRolloverPath,JSON.stringify(fixture.sourceRolloverAfter,null,2)+'\n');
  }
  const verified = await inspectPlanningFixture(fixture);
  assert.equal(verified.verified,true);
  await writeFile(fixture.checkpointPath,JSON.stringify({...fixture.operation,completedAt:fixture.now}));
  return {status:'complete'};
}

for (const stage of [0,1,2,3,4]) test(`future move interrupted after stage ${stage} resumes with one date and one decision`,async () => {
  const fixture = await seedPlanningFixture(path.resolve('.temp/recovery-flow'),stage);
  const before = await inspectPlanningFixture(fixture);
  assert.equal(before.completion,undefined);
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
  const checkpoint = JSON.parse(await readFile(fixture.checkpointPath,'utf8'));
  assert.equal(checkpoint.operation_id,fixture.ids.operation);
  assert.equal(checkpoint.event.id,fixture.ids.event);
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
    await resumeFixture(fixture);
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
  await unlink(complete.checkpointPath);
  const verified = await inspectPlanningFixture(complete);
  assert.equal(verified.verified,true);
  assert.equal(verified.checkpointRemoved,true);
});
