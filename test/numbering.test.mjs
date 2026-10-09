import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, realpath, mkdir, writeFile, rm } from 'node:fs/promises';
import path from 'node:path';
import { nextRecordNumber } from '../lib/records/numbering.mjs';
import { appendDecision } from '../lib/log/decision-log.mjs';
import { uuid7 } from '../lib/identity/identity.mjs';

async function fixture(t) {
  await mkdir(path.resolve('.temp'),{recursive:true});
  const projectsRoot = await realpath(await mkdtemp(path.join(path.resolve('.temp'),'numbering-')));
  t.after(()=>rm(projectsRoot,{recursive:true,force:true}));
  const parentId = uuid7();
  await writeFile(path.join(projectsRoot,'milestone.md'),`---\nid: ${parentId}\ntype: milestone\n---\n# Milestone\n`);
  return {projectsRoot,parentId,type:'task'};
}
const event = snapshot=>({id:uuid7(),operation_id:uuid7(),action:'task.cancelled',record_ids:[snapshot.id],actor:{kind:'person',id:'person@example.test'},activity_at:'2026-10-09T10:00:00Z',recorded_at:'2026-10-09T10:00:00Z',time_defaulted:false,before:snapshot,after:{...snapshot,state:'cancelled'}});
test('allocator retains cancelled and removed labels and scopes live records to their parent',async t=>{
  const input = await fixture(t);
  await writeFile(path.join(input.projectsRoot,'t4-cancelled.md'),`---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\ntask-state: cancelled\n---\n`);
  await writeFile(path.join(input.projectsRoot,'t99-other.md'),`---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${uuid7()}\n---\n`);
  const snapshot = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t7-retired.md'};
  await appendDecision({projectsRoot:input.projectsRoot,entry:event(snapshot)});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,8);
  assert.deepEqual(result.usedNumbers,[4,7]);
  assert.deepEqual(result.diagnostics,[]);
});
test('allocator blocks unknown retired numbers rather than interpreting prose as facts',async t=>{
  const input = await fixture(t);
  const entry = event({id:uuid7()});
  entry.before = {note:'retired t17'};
  await appendDecision({projectsRoot:input.projectsRoot,entry});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,null);
  assert.equal(result.diagnostics[0].code,'history-numbering-ambiguous');
});
test('selection moves do not masquerade as retired record labels',async t=>{
  const input = await fixture(t);
  const entry = event({id:uuid7()});
  entry.action = 'selection-move';
  entry.before = {date:'2026.10.09'};
  entry.after = {date:'2026.10.10'};
  await appendDecision({projectsRoot:input.projectsRoot,entry});
  assert.equal((await nextRecordNumber(input)).number,1);
});
test('allocator queries beyond the first history page',async t=>{
  const input = await fixture(t);
  const directory = path.join(input.projectsRoot,'.daily-tasks');
  await mkdir(directory);
  const entries = Array.from({length:1001},(_,index)=>event({id:uuid7(),type:'task',milestone_id:input.parentId,path:`t${index+1}-retired.md`}));
  await writeFile(path.join(directory,'2026.10.09-decisions.json'),JSON.stringify({schema_version:1,created_at:'2026-10-09T10:00:00Z',entries}));
  const result = await nextRecordNumber(input);
  assert.equal(result.number,1002);
  assert.equal(result.usedNumbers.length,1001);
});

test('concrete project cancellation and rename history leaves numbering available',async t=>{
  const input = await fixture(t);
  const projectId = uuid7();
  await writeFile(path.join(input.projectsRoot,'project-index.md'),`---\nid: ${projectId}\ntype: project\n---\n`);
  for (const id of [projectId,uuid7()]) {
    const snapshot = {id,type:'project',path:'old-project/project-index.md'};
    for (const action of ['project.cancelled','project.renamed']) {
      const entry = event(snapshot);
      entry.action = action;
      entry.after = {...snapshot,path:'new-project/project-index.md'};
      await appendDecision({projectsRoot:input.projectsRoot,entry});
    }
  }
  assert.equal((await nextRecordNumber(input)).number,1);
  assert.equal((await nextRecordNumber({...input,type:'milestone',parentId:projectId})).number,1);
});

test('legacy live and retired unnumbered records permit first label allocation',async t=>{
  const input = await fixture(t);
  const id = uuid7();
  await writeFile(path.join(input.projectsRoot,'legacy-task.md'),`---\nid: ${id}\ntype: task\nmilestone_id: ${input.parentId}\n---\n`);
  const snapshot = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'legacy-retired-task.md'};
  const entry = event(snapshot);
  entry.action = 'task.migrated';
  entry.after = {...snapshot,path:'t3-migrated.md',record_version:'2'};
  await appendDecision({projectsRoot:input.projectsRoot,entry});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,4);
  assert.deepEqual(result.usedNumbers,[3]);
});

test('versioned unnumbered and malformed numeric labels still block allocation',async t=>{
  const input = await fixture(t);
  for (const [name,version] of [['unnumbered.md','record_version: 2\n'],['t0-invalid.md','']]) {
    const filename = path.join(input.projectsRoot,name);
    await writeFile(filename,`---\nid: ${uuid7()}\ntype: task\nmilestone_id: ${input.parentId}\n${version}---\n`);
    const result = await nextRecordNumber(input);
    assert.equal(result.number,null);
    assert.ok(result.diagnostics.some(item=>item.code === 'invalid-numbering-label'));
    await rm(filename);
  }
});

test('artifact rename paths in holding areas or outside projects do not retire labels',async t=>{
  const input = await fixture(t);
  for (const [before,after] of [
    ['project/m1-work/inputs/source.txt','project/m1-work/inputs/renamed.txt'],
    ['project/m1-work/legacy-task/outputs/source.txt','project/m1-work/legacy-task/outputs/renamed.txt'],
    [path.resolve(input.projectsRoot,'..','external.txt'),path.resolve(input.projectsRoot,'..','external-new.txt')]
  ]) {
    const entry = event({id:uuid7()});
    entry.action = 'artifact.renamed';
    entry.before = {path:before};
    entry.after = {path:after};
    await appendDecision({projectsRoot:input.projectsRoot,entry});
  }
  assert.equal((await nextRecordNumber(input)).number,1);
  const mislabelled = event({id:uuid7()});
  mislabelled.action = 'artifact.renamed';
  mislabelled.before = {path:'project/m1-work/t7-task.md'};
  mislabelled.after = {path:'project/m1-work/t7-new.md'};
  await appendDecision({projectsRoot:input.projectsRoot,entry:mislabelled});
  assert.equal((await nextRecordNumber(input)).number,null);
});

test('descriptive artifact renames require proven holding-area paths on both sides',async t=>{
  const input = await fixture(t);
  const entry = event({id:uuid7()});
  entry.action = 'rename-headline-output';
  entry.before = {path:path.join(input.projectsRoot,'project','m1-work','outputs','headline.md')};
  entry.after = {path:path.join(input.projectsRoot,'project','m1-work','outputs','career-headline.md')};
  await appendDecision({projectsRoot:input.projectsRoot,entry});
  assert.equal((await nextRecordNumber(input)).number,1);
  const unsafe = {...entry,id:uuid7(),operation_id:uuid7(),after:{path:'project/m1-work/t9-task.md'}};
  await appendDecision({projectsRoot:input.projectsRoot,entry:unsafe});
  assert.equal((await nextRecordNumber(input)).number,null);
});

test('concrete records wrappers preserve labels for every affected cancelled record',async t=>{
  const input = await fixture(t);
  const records = [2,8].map(number=>({id:uuid7(),type:'task',milestone_id:input.parentId,path:`t${number}-cancelled.md`}));
  const entry = event(records[0]);
  entry.record_ids = records.map(record=>record.id);
  entry.before = {records};
  entry.after = {records:records.map(record=>({...record,state:'cancelled'}))};
  await appendDecision({projectsRoot:input.projectsRoot,entry});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,9);
  assert.deepEqual(result.usedNumbers,[2,8]);
});

test('mixed cancellation and acceptance reserves existing and newly allocated labels',async t=>{
  const input = await fixture(t);
  const existing = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t1-old.md'};
  const created = {...existing,id:uuid7(),path:'t3-new.md'};
  const original = event(existing);
  original.action = 'task.cancel-and-accept';
  original.record_ids = [existing.id,created.id];
  original.before = {records:[existing]};
  original.after = {records:[{...existing,state:'cancelled'},created]};
  await appendDecision({projectsRoot:input.projectsRoot,entry:original});
  const correction = {...event(existing),action:'history.snapshot-correction',corrects:original.id,
    record_ids:original.record_ids,before:[existing],after:[{...existing,state:'cancelled'},created]};
  await appendDecision({projectsRoot:input.projectsRoot,entry:correction});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,4);
  assert.deepEqual(result.usedNumbers,[1,3]);
});

test('ordinary retirement batches cannot substitute after-only identities for prior labels',async t=>{
  for (const action of ['task.cancelled','task.migrated']) {
    const input = await fixture(t);
    const existing = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t1-old.md'};
    const omitted = {...existing,id:uuid7(),path:'t3-after.md'};
    const entry = {...event(existing),action,record_ids:[existing.id,omitted.id],
      before:{records:[existing]},after:{records:[existing,omitted]}};
    await appendDecision({projectsRoot:input.projectsRoot,entry});
    const result = await nextRecordNumber(input);
    assert.equal(result.number,null);
    assert.deepEqual(result.usedNumbers,[1,3]);
    assert.ok(result.diagnostics.some(item=>item.code === 'history-numbering-ambiguous'));
    const correction = {...event(existing),action:'history.snapshot-correction',corrects:entry.id,
      record_ids:entry.record_ids,before:{records:[existing,{...omitted,path:'t4-before.md'}]},
      after:entry.after};
    await appendDecision({projectsRoot:input.projectsRoot,entry:correction});
    const corrected = await nextRecordNumber(input);
    assert.equal(corrected.number,5);
    assert.deepEqual(corrected.usedNumbers,[1,3,4]);
  }
});

test('concrete unnumbered legacy DoD retirement does not poison parent-local allocation',async t=>{
  for (const kind of ['valid','missing-parent','numeric-path']) {
    const input = await fixture(t);
    const task = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t7-existing.md'};
    const dod = {id:uuid7(),type:'dod',milestone_id:input.parentId,path:'legacy/definition-of-done.md'};
    if (kind === 'missing-parent') delete dod.milestone_id;
    if (kind === 'numeric-path') dod.path = 'legacy/t8-ambiguous.md';
    const entry = {...event(task),action:'workspace.migration',record_ids:[task.id,dod.id],
      before:{records:[task,dod]},after:{records:[task],retired_dod_id:dod.id}};
    await appendDecision({projectsRoot:input.projectsRoot,entry});
    const result = await nextRecordNumber(input);
    assert.equal(result.number,kind === 'valid' ? 8 : null);
    assert.deepEqual(result.usedNumbers,[7]);
    const unrelated = uuid7();
    await writeFile(path.join(input.projectsRoot,'other-milestone.md'),`---\nid: ${unrelated}\ntype: milestone\n---\n`);
    assert.equal((await nextRecordNumber({...input,parentId:unrelated})).number,kind === 'valid' ? 1 : null);
  }
});

test('planned or label-only snapshots cannot stand in for observed prior records',async t=>{
  for (const snapshot_kind of ['planned destination','label facts']) {
    const input = await fixture(t);
    const record = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t4-prior.md'};
    const entry = {...event(record),before:{...record,snapshot_kind}};
    await appendDecision({projectsRoot:input.projectsRoot,entry});
    const result = await nextRecordNumber(input);
    assert.equal(result.number,null);
    assert.ok(result.diagnostics.some(item=>item.code === 'history-numbering-ambiguous'));
  }
});

test('later-page correction chains enrich missing cancellation facts without rewriting history',async t=>{
  const input = await fixture(t);
  const snapshot = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t17-retired.md'};
  const original = event(snapshot);
  original.before = {note:'record retired, details omitted'};
  original.after = {id:snapshot.id,state:'cancelled'};
  const partial = event(snapshot);
  partial.action = 'metadata.corrected';
  partial.corrects = original.id;
  partial.before = {id:snapshot.id,type:'task',milestone_id:input.parentId};
  partial.after = {id:snapshot.id,type:'task',milestone_id:input.parentId};
  const correction = event(snapshot);
  correction.action = 'metadata.corrected';
  correction.corrects = partial.id;
  const fillers = Array.from({length:999},()=>({...event({id:uuid7()}),action:'task.accepted',before:null,after:null}));
  const directory = path.join(input.projectsRoot,'.daily-tasks');
  await mkdir(directory);
  const entries = [original,...fillers,partial,correction];
  await writeFile(path.join(directory,'2026.10.09-decisions.json'),JSON.stringify({schema_version:1,created_at:'2026-10-09T10:00:00Z',entries}));
  const result = await nextRecordNumber(input);
  assert.equal(result.number,18);
  assert.deepEqual(result.usedNumbers,[17]);
});

test('corrections cannot change known labels or omit affected record coverage',async t=>{
  const input = await fixture(t);
  const snapshot = {id:uuid7(),type:'task',milestone_id:input.parentId,path:'t6-retired.md'};
  const original = event(snapshot);
  await appendDecision({projectsRoot:input.projectsRoot,entry:original});
  const correction = event({...snapshot,path:'t9-retired.md'});
  correction.action = 'metadata.corrected';
  correction.corrects = original.id;
  await appendDecision({projectsRoot:input.projectsRoot,entry:correction});
  const result = await nextRecordNumber(input);
  assert.equal(result.number,null);
  assert.deepEqual(result.usedNumbers,[6,9]);
  assert.ok(result.diagnostics.some(item=>item.code === 'history-numbering-ambiguous'));
  const missing = event({id:uuid7()});
  missing.before = null;
  missing.after = null;
  missing.record_ids.push(uuid7());
  await appendDecision({projectsRoot:input.projectsRoot,entry:missing});
  const incomplete = event({id:missing.record_ids[0],type:'task',milestone_id:input.parentId,path:'t12-retired.md'});
  incomplete.action = 'metadata.corrected';
  incomplete.corrects = missing.id;
  await appendDecision({projectsRoot:input.projectsRoot,entry:incomplete});
  const blocked = await nextRecordNumber(input);
  assert.equal(blocked.number,null);
  assert.ok(blocked.diagnostics.some(item=>item.source === missing.id));
});
