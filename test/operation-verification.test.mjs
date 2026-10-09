import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, realpath, writeFile, readFile, access, symlink, unlink, rmdir } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { tmpdir } from 'node:os';
import { uuid7 } from '../lib/identity/identity.mjs';
import { resolveContext } from '../lib/profile/context.mjs';
import { appendDecision } from '../lib/log/decision-log.mjs';
import { verifyOperation, completeOperation, completeChangedRollover, inspectMigrationRetirement, completeMigration } from '../lib/operations/verification.mjs';

const hash = text => createHash('sha256').update(text).digest('hex');
const execute = promisify(execFile);
async function fixture() {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/operation-verification-')));
  const input = {vaultRoot:root,homeRoot:root,now:'2026-10-09T15:00:00Z'};
  const state = path.join(root,'.nyssaai/daily-tasks');
  await mkdir(path.join(state,'operations'),{recursive:true});
  await mkdir(path.join(root,'projects'),{recursive:true});
  await mkdir(path.join(root,'daily'),{recursive:true});
  await writeFile(path.join(state,'profile.json'),JSON.stringify({schema_version:1,user:{name:'Example',email:'owner@example.test'},timezone:'America/Chicago',priorities:[],vaultRoot:'.',projectsRoot:'./projects',dailyPlansRelative:'daily'}));
  const context = await resolveContext(input), id = uuid7();
  input.operationPath = path.join(state,'operations',`${id}.json`);
  const file = path.join(root,'projects','task.md');
  const event = {id:uuid7(),operation_id:id,action:'update',record_ids:[],actor:{kind:'person',id:'owner@example.test'},activity_at:input.now,recorded_at:input.now,time_defaulted:false};
  const operation = {schemaVersion:2,operation_id:id,contextBinding:context.planningBinding,event,files:[{path:file,before:hash('before'),after:hash('after')}]};
  const save = () => writeFile(input.operationPath,JSON.stringify(operation));
  await save();
  return {input,context,operation,event,file,save};
}

test('packaged completion checks actual evidence from an unrelated working directory', async () => {
  const f = await fixture();
  const inputFile = path.join(f.context.vaultRoot,'input.json');
  await writeFile(inputFile,JSON.stringify(f.input));
  await writeFile(f.file,'after');
  for (const entry of ['artifacts/portable/bin/daily-tasks.mjs','artifacts/cowork/scripts/daily-tasks.mjs']) {
    const result = await execute(process.execPath,[path.resolve(entry),'operation-complete','--input',inputFile],{cwd:tmpdir()});
    assert.equal(JSON.parse(result.stdout).status,'pending');
    await access(f.input.operationPath);
  }
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  const result = await execute(process.execPath,[path.resolve('artifacts/portable/bin/daily-tasks.mjs'),'operation-complete','--input',inputFile],{cwd:tmpdir()});
  assert.equal(JSON.parse(result.stdout).status,'completed');
  await assert.rejects(access(f.input.operationPath),{code:'ENOENT'});
});

test('actual bytes and exact event determine pending, conflict and completion', async () => {
  const f = await fixture();
  await writeFile(f.file,'before');
  assert.equal((await verifyOperation(f.input)).status,'pending');
  await writeFile(f.file,'unexpected');
  assert.equal((await completeOperation(f.input)).status,'conflict');
  await access(f.input.operationPath);
  await writeFile(f.file,'after');
  assert.equal((await verifyOperation(f.input)).status,'pending');
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  assert.equal((await completeOperation({...f.input,dryRun:true})).status,'preview');
  await access(f.input.operationPath);
  f.operation.baseline = {beforeHash:null,value:{schemaVersion:1,records:{}}};
  await f.save();
  assert.equal((await completeOperation(f.input)).status,'completed');
  assert.deepEqual(JSON.parse(await readFile(path.join(f.context.stateRoot,'reconciliation.json'),'utf8')),f.operation.baseline.value);
  await assert.rejects(access(f.input.operationPath),{code:'ENOENT'});
});

test('verification rejects forged evidence, escaped effects and another binding', async () => {
  const f = await fixture();
  await assert.rejects(verifyOperation({...f.input,actual:{}}),/Caller-supplied/);
  f.operation.files[0].path = path.join(f.context.projectsRoot,'.daily-tasks','history.json');
  await f.save();
  await assert.rejects(verifyOperation(f.input),/Effect path/);
  f.operation.files[0].path = f.file;
  f.operation.contextBinding = '0'.repeat(64);
  await f.save();
  await assert.rejects(verifyOperation(f.input),/bound/);
});

test('conflicting event and changed baseline never clear checkpoint', async () => {
  const f = await fixture();
  await writeFile(f.file,'after');
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:{...f.event,action:'different'}});
  assert.equal((await completeOperation(f.input)).status,'conflict');
  await access(f.input.operationPath);
  const g = await fixture();
  await writeFile(g.file,'after');
  await appendDecision({projectsRoot:g.context.projectsRoot,entry:g.event});
  g.operation.baseline = {beforeHash:null,value:{schemaVersion:1,records:{}}};
  await g.save();
  await writeFile(path.join(g.context.stateRoot,'reconciliation.json'),'{}');
  await assert.rejects(completeOperation(g.input),/Baseline changed/);
  await access(g.input.operationPath);
});

test('changed rollover fails closed without original source evidence', async () => {
  const f = await fixture();
  f.operation.rollover = {date:f.context.localDate,planId:uuid7(),expectedSelectedIds:[]};
  await f.save();
  await assert.rejects(completeOperation(f.input),/Specialized/);
  await assert.rejects(completeChangedRollover(f.input),/original plan/);
});

test('verification includes events after the first page without filtering record identities', async () => {
  const f = await fixture();
  await writeFile(f.file,'after');
  const entries = Array.from({length:1000},() => ({...f.event,id:uuid7(),operation_id:uuid7()}));
  entries.push({...f.event,record_ids:[uuid7()]});
  const directory = path.join(f.context.projectsRoot,'.daily-tasks');
  await mkdir(directory);
  await writeFile(path.join(directory,'2026.10.09-decisions.json'),JSON.stringify({schema_version:1,created_at:f.input.now,entries}));
  assert.equal((await verifyOperation(f.input)).status,'conflict');
});

test('symlink ancestors and changed protected files are rejected', async () => {
  const f = await fixture();
  const outside = path.join(f.context.vaultRoot,'outside');
  await mkdir(outside);
  await writeFile(path.join(outside,'task.md'),'after');
  const link = path.join(f.context.projectsRoot,'linked');
  await symlink(outside,link,process.platform === 'win32' ? 'junction' : 'dir');
  f.operation.files[0].path = path.join(link,'task.md');
  await f.save();
  await assert.rejects(verifyOperation(f.input),/Unsafe directory/);
  f.operation.files[0].path = f.file;
  await writeFile(f.file,'after');
  const protection = path.join(f.context.dailyPlansRoot,'old.md');
  await writeFile(protection,'modified');
  f.operation.protectedFiles = [{path:protection,sha256:hash('old')}];
  await f.save();
  assert.equal((await verifyOperation(f.input)).status,'conflict');
});

test('already-written matching baseline permits completion retry', async () => {
  const f = await fixture();
  await writeFile(f.file,'after');
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  f.operation.baseline = {beforeHash:null,value:{schemaVersion:1,records:{}}};
  await f.save();
  await writeFile(path.join(f.context.stateRoot,'reconciliation.json'),JSON.stringify(f.operation.baseline.value));
  assert.equal((await completeOperation(f.input)).status,'completed');
});

test('migration retirement sees live legacy copies pointing to headings', async () => {
  const f = await fixture(), criterionId = uuid7();
  const source = `---\nid: ${uuid7()}\ntype: dod\n---\n# Definition of Done\n- [x] Criterion\n  <!-- id: ${criterionId} -->\n\nHistory preserved.\n`;
  const destination = `---\nid: ${uuid7()}\ntype: task\n---\n# Task\n## Definition of Done\n- [x] Criterion\n  <!-- id: ${criterionId} -->\n\nHistory preserved.\n`;
  const retiringPath = path.join(f.context.projectsRoot,'definition-of-done.md');
  await writeFile(retiringPath,source);
  await writeFile(f.file,destination);
  f.operation.migration = {retiringPath,destinationPath:f.file,sourceHash:hash(source),expectedCriteria:[{id:criterionId,text:'Criterion',checked:true}],preservedFields:{}};
  await f.save();
  const legacy = path.join(f.context.projectsRoot,'legacy-copy.md');
  await writeFile(legacy,'[Done](definition-of-done.md#criterion)');
  const result = await inspectMigrationRetirement(f.input);
  assert.equal(result.allowed,false);
  assert.ok(result.issues.some(issue => issue.reason === 'live-incoming-link' && issue.path === legacy));
  await access(retiringPath);
  for (const markdown of ['[Done](definition-of-done.md "title")','[Done](<definition-of-done.md#criterion> "title")','[Done][done]\n[done]: <definition-of-done.md> "title"']) {
    await writeFile(legacy,markdown);
    assert.ok((await inspectMigrationRetirement(f.input)).issues.some(issue=>issue.reason === 'live-incoming-link'));
  }
  await writeFile(legacy,`- [ ] [[task|Done]] <!-- ref: ${source.match(/id: ([^\n]+)/)[1]} -->`);
  assert.ok((await inspectMigrationRetirement(f.input)).issues.some(issue=>issue.reason === 'live-incoming-reference'));
  await writeFile(legacy,'No retired links.');
  const projectNamedInputs = path.join(f.context.projectsRoot,'inputs');
  await mkdir(projectNamedInputs);
  // The project-root inputs folder is ordinary storage, not a milestone holding area.
  await writeFile(path.join(projectNamedInputs,'legacy.md'),'[Done](../definition-of-done.md)');
  assert.ok((await inspectMigrationRetirement(f.input)).issues.some(issue=>issue.reason === 'live-incoming-link'));
  await unlink(path.join(projectNamedInputs,'legacy.md'));
  await rmdir(f.context.dailyPlansRoot);
  assert.equal((await inspectMigrationRetirement(f.input)).allowed,true);
});

test('rollover carries nonempty membership, preserves removals and finishes pending state next day', async () => {
  const f = await fixture(), projectId = uuid7(), milestoneId = uuid7(), taskId = uuid7(), removedId = uuid7(), planId = uuid7(), previousPlanId = uuid7();
  const project = path.join(f.context.projectsRoot,'demo'), milestone = path.join(project,'m1-work');
  await mkdir(milestone,{recursive:true});
  const doc = (id,type,title,extra='',body='') => `---\nid: ${id}\ntype: ${type}\ntitle: ${title}\nowner: owner@example.test\n${type}-state: not-started\ncreated_at: ${f.input.now}\nupdated_at: ${f.input.now}\n${extra}---\n# ${title}\n${body}`;
  await writeFile(path.join(project,'project-index.md'),doc(projectId,'project','Demo','',`- [ ] [[m1-work/m1-work|Work]] <!-- ref: ${milestoneId} -->\n`));
  await writeFile(path.join(milestone,'m1-work.md'),doc(milestoneId,'milestone','Work',`project_id: ${projectId}\n`,`- [ ] [[t1-work|A]] <!-- ref: ${taskId} -->\n- [ ] [[t2-removed|B]] <!-- ref: ${removedId} -->\n`));
  const taskSources = [];
  for (const [id,name] of [[taskId,'t1-work'],[removedId,'t2-removed']]) {
    const filename = path.join(milestone,`${name}.md`), text = doc(id,'task',name,`project_id: ${projectId}\nmilestone_id: ${milestoneId}\n`);
    await writeFile(filename,text); taskSources.push({path:filename,sha256:hash(text)});
  }
  const header = `---\nid: ${planId}\ntype: daily-plan\ncreated_at: ${f.input.now}\n---\n# Today\n`;
  const row = id => `- [ ] Work <!-- ref: ${id} -->\n`;
  const after = header + row(taskId), currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const previousPath = path.join(f.context.dailyPlansRoot,'2026.10.08-daily-plan.md');
  const previous = `---\nid: ${previousPlanId}\ntype: daily-plan\n---\n# Yesterday\n${row(taskId)}${row(removedId)}`;
  await writeFile(currentPath,after); await writeFile(previousPath,previous);
  f.operation.files = [{path:currentPath,before:hash(header),after:hash(after)}];
  f.operation.rollover = {date:'2026.10.09',planId,previousPlanId,expectedCreatedAt:f.input.now,removedIds:[removedId],expectedSelectedIds:[taskId],previousPath,previousHash:hash(previous),sourceSnapshot:{currentMarkdown:header,taskSources}};
  await f.save(); await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  f.operation.rollover.expectedSelectedIds = []; await f.save();
  await assert.rejects(completeChangedRollover(f.input),/membership/); await access(f.input.operationPath);
  f.operation.rollover.expectedSelectedIds = [taskId]; await f.save();
  const target = path.join(f.context.stateRoot,'rollover','2026.10.09.json');
  await mkdir(path.dirname(target));
  const pendingState = JSON.stringify({schemaVersion:1,date:'2026.10.09',planId,removedIds:[removedId]});
  await writeFile(target,pendingState);
  f.operation.rollover.expectedStateHash = '0'.repeat(64); await f.save();
  await assert.rejects(completeChangedRollover(f.input),/state changed since checkpoint/);
  f.operation.rollover.expectedStateHash = hash(pendingState); await f.save();
  assert.equal((await completeChangedRollover({...f.input,now:'2026-10-10T15:00:00Z'})).status,'completed');
  assert.deepEqual(JSON.parse(await readFile(target,'utf8')).removedIds,[removedId]);
  assert.equal(await readFile(currentPath,'utf8'),after);
});

test('first-plan rollover proves absence of earlier plans', async () => {
  const f = await fixture(), planId = uuid7(), currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const after = `---\nid: ${planId}\ntype: daily-plan\ncreated_at: ${f.input.now}\n---\n# Today\n`;
  await writeFile(currentPath,after);
  f.operation.files = [{path:currentPath,before:null,after:hash(after)}];
  f.operation.rollover = {date:f.context.localDate,planId,previousPlanId:null,previousPath:null,previousHash:null,expectedCreatedAt:f.input.now,removedIds:[],expectedSelectedIds:[],sourceSnapshot:{currentMarkdown:null,taskSources:[]}};
  await f.save(); await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  assert.equal((await completeChangedRollover(f.input)).status,'completed');
});

test('changed rollover verifies preserved plan identity and prior bytes before receipt', async () => {
  const f = await fixture(), planId = uuid7(), previousPlanId = uuid7();
  const createdAt = '2026-10-09T12:00:00Z';
  const original = `---\nid: ${planId}\ntype: daily-plan\ncreated_at: ${createdAt}\n---\n# Today\n`;
  const after = original+'\nPreserved planning note.\n';
  const previous = `---\nid: ${previousPlanId}\ntype: daily-plan\ncreated_at: 2026-10-08T12:00:00Z\n---\n# Yesterday\n`;
  const currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const previousPath = path.join(f.context.dailyPlansRoot,'2026.10.08-daily-plan.md');
  await writeFile(currentPath,after);
  await writeFile(previousPath,previous);
  f.operation.files = [{path:currentPath,before:hash(original),after:hash(after)}];
  f.operation.rollover = {date:f.context.localDate,planId,previousPlanId,expectedCreatedAt:createdAt,removedIds:[],expectedSelectedIds:[],previousPath,previousHash:hash(previous),sourceSnapshot:{currentMarkdown:original,taskSources:[]}};
  await f.save();
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  assert.equal((await completeChangedRollover({...f.input,dryRun:true})).status,'preview');
  await assert.rejects(access(path.join(f.context.stateRoot,'rollover','2026.10.09.json')),{code:'ENOENT'});
  const target = path.join(f.context.stateRoot,'rollover','2026.10.09.json');
  await mkdir(path.dirname(target));
  const priorReceipt = {schemaVersion:1,date:'2026.10.09',planId,operationId:f.operation.operation_id,completedAt:'2026-10-09T14:30:00Z',removedIds:[]};
  const priorBytes = JSON.stringify(priorReceipt);
  await writeFile(target,priorBytes);
  f.operation.baseline = {beforeHash:null,value:{schemaVersion:1,records:{}}}; await f.save();
  const baselinePath = path.join(f.context.stateRoot,'reconciliation.json');
  await writeFile(baselinePath,'{}');
  await assert.rejects(completeChangedRollover(f.input),/Baseline changed/);
  await access(f.input.operationPath);
  assert.equal(await readFile(target,'utf8'),priorBytes);
  await unlink(baselinePath);
  assert.equal((await completeChangedRollover(f.input)).status,'completed');
  const receipt = JSON.parse(await readFile(path.join(f.context.stateRoot,'rollover','2026.10.09.json'),'utf8'));
  assert.equal(receipt.operationId,f.operation.operation_id);
  assert.equal(receipt.completedAt,priorReceipt.completedAt);
  assert.deepEqual(JSON.parse(await readFile(baselinePath,'utf8')),f.operation.baseline.value);
  assert.equal(await readFile(previousPath,'utf8'),previous);
});

test('new-plan rollover proves null before evidence and the actual prior identity', async () => {
  const f = await fixture(), planId = uuid7(), previousPlanId = uuid7();
  const createdAt = f.input.now;
  const after = `---\nid: ${planId}\ntype: daily-plan\ncreated_at: ${createdAt}\n---\n# Today\n`;
  const previous = `---\nid: ${previousPlanId}\ntype: daily-plan\n---\n# Yesterday\n`;
  const currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const previousPath = path.join(f.context.dailyPlansRoot,'2026.10.08-daily-plan.md');
  await writeFile(currentPath,after);
  await writeFile(previousPath,previous);
  f.operation.files = [{path:currentPath,before:null,after:hash(after)}];
  f.operation.rollover = {date:f.context.localDate,planId,previousPlanId,expectedCreatedAt:createdAt,removedIds:[],expectedSelectedIds:[],previousPath,previousHash:hash(previous),sourceSnapshot:{currentMarkdown:null,taskSources:[]}};
  await f.save();
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  f.operation.rollover.previousPlanId = uuid7();
  await f.save();
  await assert.rejects(completeChangedRollover(f.input),/Previous plan identity/);
  f.operation.rollover.previousPlanId = previousPlanId;
  const taskShapedPrevious = previous.replace('type: daily-plan','type: task');
  await writeFile(previousPath,taskShapedPrevious);
  f.operation.rollover.previousHash = hash(taskShapedPrevious);
  await f.save();
  await assert.rejects(completeChangedRollover(f.input),/Previous plan identity or type/);
  await writeFile(previousPath,previous);
  f.operation.rollover.previousHash = hash(previous);
  await f.save();
  assert.equal((await completeChangedRollover(f.input)).status,'completed');
});

test('baseline checks actual canonical fields, view hashes and preserves unrelated entries', async () => {
  const f = await fixture(), taskId = uuid7(), unrelatedId = uuid7();
  const task = `---\nid: ${taskId}\ntype: task\ntask-state: not-started\nowner: owner@example.test\n---\n# Task\n`;
  await writeFile(f.file,task);
  f.operation.files[0].after = hash(task);
  const view = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  await writeFile(view,'# Today\n');
  f.operation.files.push({path:view,before:null,after:hash('# Today\n')});
  const beforeText = JSON.stringify({schemaVersion:1,records:{[unrelatedId]:{canonical:{state:'not-started'},views:{}}}});
  await writeFile(path.join(f.context.stateRoot,'reconciliation.json'),beforeText);
  f.operation.baseline = {beforeHash:hash(beforeText),beforeText,value:{schemaVersion:1,records:{...JSON.parse(beforeText).records,[taskId]:{canonical:{state:'completed'},views:{[view]:{selected:false,hash:hash('# Today\n')}}}}}};
  await f.save();
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  await assert.rejects(completeOperation(f.input),/canonical field/);
  f.operation.baseline.value.records[taskId].canonical.state = 'not-started';
  f.operation.baseline.value.records[taskId].views[view].hash = '0'.repeat(64);
  await f.save();
  await assert.rejects(completeOperation(f.input),/view hash/);
  f.operation.baseline.value.records[taskId].views[view].hash = hash('# Today\n');
  delete f.operation.baseline.value.records[unrelatedId];
  await f.save();
  await assert.rejects(completeOperation(f.input),/cannot retire records/);
  f.operation.baseline.value.records[unrelatedId] = JSON.parse(beforeText).records[unrelatedId];
  await f.save();
  assert.equal((await completeOperation(f.input)).status,'completed');
});

test('migration post-delete completion verifies snapshot preservation and clears checkpoint only', async () => {
  const f = await fixture(), criterionId = uuid7();
  const source = `---\nid: ${uuid7()}\ntype: dod\n---\n# Definition of Done\n- [x] Criterion\n  <!-- id: ${criterionId} -->\n\nHistory preserved.\n`;
  const destination = `---\nid: ${uuid7()}\ntype: task\n---\n# Task\n## Definition of Done\n- [x] Criterion\n  <!-- id: ${criterionId} -->\n\nHistory preserved.\n`;
  const retiringPath = path.join(f.context.projectsRoot,'definition-of-done.md');
  await writeFile(retiringPath,source);
  await writeFile(f.file,destination);
  f.operation.files = [{path:retiringPath,before:hash(source),after:null},{path:f.file,before:hash('before'),after:hash(destination)}];
  f.operation.migration = {retiringPath,destinationPath:f.file,sourceHash:hash(source),expectedCriteria:[{id:criterionId,text:'Criterion',checked:true}],preservedFields:{}};
  f.operation.sourceSnapshot = {retiringMarkdown:source};
  const retiringId = source.match(/id: ([^\n]+)/)[1], destinationId = destination.match(/id: ([^\n]+)/)[1], unrelatedId = uuid7();
  const beforeText = JSON.stringify({schemaVersion:1,records:{[retiringId]:{canonical:{type:'dod'},views:{}},[unrelatedId]:{canonical:{type:'project'},views:{}}}});
  await writeFile(path.join(f.context.stateRoot,'reconciliation.json'),beforeText);
  f.operation.baseline = {beforeHash:hash(beforeText),beforeText,value:{schemaVersion:1,records:{[destinationId]:{canonical:{type:'task'},views:{}},[unrelatedId]:JSON.parse(beforeText).records[unrelatedId]}}};
  await f.save();
  assert.equal((await inspectMigrationRetirement(f.input)).allowed,true);
  await unlink(retiringPath);
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  for (const changed of [destination.replace('[x] Criterion','[ ] Criterion'),destination.replace('Criterion','Different'),destination.replace('History preserved.','')]) {
    await writeFile(f.file,changed);
    f.operation.files.find(file=>file.path === f.file).after = hash(changed); await f.save();
    assert.equal((await completeMigration(f.input)).status,'conflict');
    await access(f.input.operationPath);
  }
  await writeFile(f.file,destination);
  f.operation.files.find(file=>file.path === f.file).after = hash(destination); await f.save();
  assert.equal((await completeMigration({...f.input,dryRun:true})).status,'preview');
  await access(f.input.operationPath);
  assert.equal((await completeMigration(f.input)).status,'completed');
  assert.equal(await readFile(f.file,'utf8'),destination);
  const baseline = JSON.parse(await readFile(path.join(f.context.stateRoot,'reconciliation.json'),'utf8'));
  assert.equal(Object.hasOwn(baseline.records,retiringId),false);
  assert.deepEqual(baseline.records[unrelatedId],JSON.parse(beforeText).records[unrelatedId]);
});

