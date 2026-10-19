import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, realpath, writeFile, readFile, access, symlink, unlink, rmdir } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { tmpdir } from 'node:os';
import { uuid7 } from '#core/identity/identity.mjs';
import { resolveContext } from '#core/profile/context.mjs';
import { appendDecision, queryDecisions } from '#core/log/decision-log.mjs';
import { verifyOperation, completeOperation, completeChangedRollover } from '#core/operations/verification.mjs';
import { preparePlanning, savePlanningState } from '#core/planning/session.mjs';
import { planningScreen } from './fixtures/planning-screen.mjs';

const hash = text => createHash('sha256').update(text).digest('hex');
const execute = promisify(execFile);
async function fixture() {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/operation-verification-')));
  const input = {vaultRoot:root,homeRoot:root,now:'2026-10-09T15:00:00Z'};
  const state = path.join(root,'.nyssa-ai/daily-tasks');
  input.stateRoot = state;
  await mkdir(path.join(state,'operations'),{recursive:true});
  await mkdir(path.join(root,'projects'),{recursive:true});
  await mkdir(path.join(root,'daily'),{recursive:true});
  await writeFile(path.join(state,'profile.json'),JSON.stringify({schema_version:2,user:{name:'Example',email:'owner@example.test'},timezone:'America/Chicago',priorities:[],vaultRoot:'.',projectsRoot:'./projects',dailyPlansRelative:'daily'}));
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

test('actual bytes and exact event determine pending, conflict and completion (including forward-slash operationPath)', async () => {
  const f = await fixture();
  const slashInput = {...f.input,operationPath:f.input.operationPath.replaceAll('\\','/')};
  await writeFile(f.file,'before');
  assert.equal((await verifyOperation(slashInput)).status,'pending');
  await writeFile(f.file,'unexpected');
  assert.equal((await completeOperation(slashInput)).status,'conflict');
  await access(f.input.operationPath);
  await writeFile(f.file,'after');
  assert.equal((await verifyOperation(slashInput)).status,'pending');
  await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  assert.equal((await completeOperation({...slashInput,dryRun:true})).status,'preview');
  await access(f.input.operationPath);
  f.operation.baseline = {beforeHash:null,value:{schemaVersion:1,records:{}}};
  await f.save();
  assert.equal((await completeOperation(slashInput)).status,'completed');
  assert.deepEqual(JSON.parse(await readFile(path.join(f.context.stateRoot,'reconciliation.json'),'utf8')),f.operation.baseline.value);
  await assert.rejects(access(f.input.operationPath),{code:'ENOENT'});
});

test('recovery keeps custom personal and partial project sources through verification and completion', async () => {
  const f = await fixture();
  const homeRoot = path.join(f.context.vaultRoot,'synthetic-home');
  const userPath = path.join(homeRoot,'accepted-settings/profile.json');
  const projectPath = path.join(f.context.vaultRoot,'accepted-settings/profile.json');
  for (const filename of [userPath,projectPath]) await mkdir(path.dirname(filename),{recursive:true});
  await writeFile(userPath,JSON.stringify({schema_version:2,user:{name:'Example',email:'owner@example.test'},timezone:'America/Chicago',priorities:['personal']}));
  await writeFile(projectPath,JSON.stringify({schema_version:2,projectsRoot:'./projects',dailyPlansRelative:'daily',priorities:[]}));
  const configurationSources = {schemaVersion:1,user:{profilePath:userPath},project:{profilePath:projectPath}};
  const input = {...f.input,homeRoot,configurationSources};
  const context = await resolveContext(input);
  assert.deepEqual(context.configurationSources,configurationSources);
  assert.deepEqual(context.profile.priorities,[]);
  await writeFile(f.file,'before');
  assert.equal((await verifyOperation(input)).status,'pending');
  await writeFile(f.file,'after');
  await appendDecision({projectsRoot:context.projectsRoot,entry:f.event});
  assert.equal((await completeOperation({...input,configurationSources:context.configurationSources,stateRoot:context.stateRoot})).status,'completed');
  assert.equal((await queryDecisions({projectsRoot:context.projectsRoot})).total,1);
  assert.deepEqual((await resolveContext(input)).configurationSources,configurationSources);
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

test('rollover carries prior selections and omitted in-progress work, preserves removals and recovers next day', async () => {
  const f = await fixture(), projectId = uuid7(), milestoneId = uuid7(), taskId = uuid7(), removedId = uuid7(), startedId = uuid7(), planId = uuid7(), previousPlanId = uuid7();
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
  const startedPath = path.join(milestone,'t3-started.md');
  const startedText = doc(startedId,'task','Started',`project_id: ${projectId}\nmilestone_id: ${milestoneId}\nstarted_at: ${f.input.now}\n`)
    .replace('task-state: not-started','task-state: in-progress');
  await writeFile(startedPath,startedText);
  taskSources.push({path:startedPath,sha256:hash(startedText)});
  const header = `---\nid: ${planId}\ntype: daily-plan\ncreated_at: ${f.input.now}\n---\n# Today\n`;
  const row = id => `- [ ] Work <!-- ref: ${id} -->\n`;
  const after = header + row(taskId) + row(startedId).replace('[ ]','[>]'), currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const previousPath = path.join(f.context.dailyPlansRoot,'2026.10.08-daily-plan.md');
  const previous = `---\nid: ${previousPlanId}\ntype: daily-plan\n---\n# Yesterday\n${row(taskId)}${row(removedId)}`;
  await writeFile(currentPath,after); await writeFile(previousPath,previous);
  f.operation.files = [{path:currentPath,before:hash(header),after:hash(after)}];
  f.operation.rollover = {date:'2026.10.09',planId,previousPlanId,expectedCreatedAt:f.input.now,removedIds:[removedId],expectedSelectedIds:[taskId],previousPath,previousHash:hash(previous),sourceSnapshot:{currentMarkdown:header,taskSources}};
  await f.save(); await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  f.operation.rollover.expectedSelectedIds = []; await f.save();
  await assert.rejects(completeChangedRollover(f.input),/membership/); await access(f.input.operationPath);
  f.operation.rollover.expectedSelectedIds = [taskId]; await f.save();
  await assert.rejects(completeChangedRollover(f.input),/membership/);
  f.operation.rollover.expectedSelectedIds = [taskId,startedId]; await f.save();
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

test('create-plan prepares rollover, taskSources and carried review rows before today plan exists, and preserves carriedFrom after writing ↺', async () => {
  const f = await fixture(), projectId = uuid7(), milestoneId = uuid7(), taskId = uuid7(), previousPlanId = uuid7();
  await unlink(f.input.operationPath);
  const project = path.join(f.context.projectsRoot,'demo'), milestone = path.join(project,'m1-work');
  await mkdir(milestone,{recursive:true});
  const doc = (id,type,title,extra='',body='') => `---\nid: ${id}\ntype: ${type}\ntitle: ${title}\nowner: owner@example.test\n${type}-state: not-started\ncreated_at: ${f.input.now}\nupdated_at: ${f.input.now}\n${extra}---\n# ${title}\n${body}`;
  await writeFile(path.join(project,'project-index.md'),doc(projectId,'project','Demo','',`- [ ] [[m1-work/m1-work|Work]] <!-- ref: ${milestoneId} -->\n`));
  await writeFile(path.join(milestone,'m1-work.md'),doc(milestoneId,'milestone','Work',`project_id: ${projectId}\n`,`- [ ] [[t1-work|A]] <!-- ref: ${taskId} -->\n`));
  const taskFile = path.join(milestone,'t1-work.md'), taskText = doc(taskId,'task','A',`project_id: ${projectId}\nmilestone_id: ${milestoneId}\n`);
  await writeFile(taskFile,taskText);
  const previousPath = path.join(f.context.dailyPlansRoot,'2026.10.08-daily-plan.md');
  await writeFile(previousPath,`---\nid: ${previousPlanId}\ntype: daily-plan\n---\n# Yesterday\n- [ ] [[../projects/demo/m1-work/t1-work|A]] <!-- ref: ${taskId} -->\n`);
  const prepared = await preparePlanning(f.input);
  assert.equal(prepared.status,'create-plan');
  assert.ok(prepared.current.proposedId);
  assert.equal(prepared.rollover.selected.length,1);
  assert.equal(prepared.rollover.selected[0].carriedFrom,'2026.10.08');
  assert.deepEqual(prepared.rollover.taskSources,[{path:taskFile,sha256:hash(taskText)}]);
  assert.equal(prepared.review.selected[0].carriedFrom,'2026.10.08');
  const currentPath = prepared.current.path;
  const planMarkdown = `---\nid: ${prepared.current.proposedId}\ntype: daily-plan\ncreated_at: ${f.input.now}\n---\n# Today\n- [ ] ↺ [[../projects/demo/m1-work/t1-work|A]] <!-- ref: ${taskId} -->\n`;
  await writeFile(currentPath,planMarkdown);
  const reopened = await preparePlanning(f.input);
  assert.equal(reopened.status,'prepared');
  assert.equal(reopened.review.selected[0].carriedFrom,'2026.10.08');
  const savedReview = await savePlanningState({...f.input,action:'save-review',reviewMarkdown:planningScreen(reopened),
    expectedPlanHash:reopened.current.sha256,expectedPreviousHash:reopened.previous.sha256,expectedStateHash:null,
    expectedInventoryHash:reopened.inventoryHash,expectedReviewHash:reopened.reviewHash});
  assert.equal(savedReview.status,'saved');
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

test('planning classifies typed rollover dependencies without completing checkpoint, baseline or history', async () => {
  const f = await fixture(), planId = uuid7(), laterId = uuid7();
  const currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const laterPath = path.join(f.context.dailyPlansRoot,'2026.10.10-daily-plan.md');
  const markdown = id => `---\nid: ${id}\ntype: daily-plan\ncreated_at: ${f.input.now}\n---\n# Plan\n`;
  await writeFile(currentPath,markdown(planId));
  await writeFile(laterPath,markdown(laterId));
  f.operation.files = [{path:currentPath,before:null,after:hash(markdown(planId))}];
  f.operation.rollover = {date:f.context.localDate,planId,previousPlanId:null,previousPath:null,previousHash:null,
    expectedCreatedAt:f.input.now,removedIds:[],expectedSelectedIds:[],sourceSnapshot:{currentMarkdown:null,taskSources:[]}};
  const baselinePath = path.join(f.context.stateRoot,'reconciliation.json');
  const baseline = JSON.stringify({schemaVersion:1,records:{}});
  await writeFile(baselinePath,baseline);
  f.operation.baseline = {beforeHash:hash(baseline),beforeText:baseline,value:JSON.parse(baseline)};
  const targetState = path.join(f.context.stateRoot,'rollover','2026.10.09.json');
  const laterState = path.join(f.context.stateRoot,'rollover','2026.10.10.json');
  await mkdir(path.dirname(targetState));
  await writeFile(targetState,JSON.stringify({schemaVersion:1,date:'2026.10.09',planId,removedIds:[]}));
  f.operation.rollover.expectedStateHash = hash(await readFile(targetState));
  await writeFile(laterState,JSON.stringify({schemaVersion:1,date:'2026.10.10',planId:laterId,removedIds:[],operationId:uuid7(),completedAt:'2026-10-10T15:00:00Z'}));
  await f.save();
  const history = await appendDecision({projectsRoot:f.context.projectsRoot,entry:f.event});
  const paths = [f.input.operationPath,baselinePath,targetState,laterState,history.file,currentPath,laterPath];
  const before = await Promise.all(paths.map(filename => readFile(filename)));
  const overlap = await preparePlanning({...f.input,dryRun:true});
  assert.equal(overlap.status,'recovery-required');
  assert.equal(overlap.recovery.operations[0].status,'blocking');
  assert.deepEqual(overlap.recovery.operations[0].statePaths,[targetState]);
  const disjoint = await preparePlanning({...f.input,now:'2026-10-10T15:00:00Z',dryRun:true});
  assert.equal(disjoint.status,'prepared');
  assert.equal(disjoint.previous,null);
  assert.equal(disjoint.recovery.operations[0].status,'unrelated');
  assert.deepEqual(await Promise.all(paths.map(filename => readFile(filename))),before);
});

test('planning classifies typed record checkpoints and protected plan dependencies without changing recovery evidence', async () => {
  const f = await fixture(), destinationId = uuid7(), criterionId = uuid7(), projectId = uuid7(), milestoneId = uuid7();
  const currentPath = path.join(f.context.dailyPlansRoot,'2026.10.09-daily-plan.md');
  const destination = `---\nid: ${destinationId}\ntype: task\ntitle: Task\nowner: owner@example.test\ntask-state: not-started\ncreated_at: ${f.input.now}\nupdated_at: ${f.input.now}\nproject_id: ${projectId}\nmilestone_id: ${milestoneId}\n---\n# Task\n## Definition of Done\n- [ ] Criterion\n  <!-- id: ${criterionId} -->\n`;
  await writeFile(path.join(f.context.projectsRoot,'project-index.md'),`---\nid: ${projectId}\ntype: project\ntitle: Project\nowner: owner@example.test\nproject-state: not-started\ncreated_at: ${f.input.now}\nupdated_at: ${f.input.now}\n---\n- [ ] [[m1-work|Work]] <!-- ref: ${milestoneId} -->\n`);
  await writeFile(path.join(f.context.projectsRoot,'m1-work.md'),`---\nid: ${milestoneId}\ntype: milestone\ntitle: Work\nowner: owner@example.test\nmilestone-state: not-started\ncreated_at: ${f.input.now}\nupdated_at: ${f.input.now}\nproject_id: ${projectId}\n---\n- [ ] [[task|Task]] <!-- ref: ${destinationId} -->\n`);
  await writeFile(currentPath,`---\nid: ${uuid7()}\ntype: daily-plan\n---\n`);
  await writeFile(f.file,destination);
  f.event.record_ids = [destinationId];
  f.operation.files = [{path:f.file,before:hash('before'),after:hash(destination)}];
  const baselinePath = path.join(f.context.stateRoot,'reconciliation.json');
  const baseline = JSON.stringify({schemaVersion:1,records:{}});
  await writeFile(baselinePath,baseline);
  f.operation.baseline = {beforeHash:hash(baseline),beforeText:baseline,value:{schemaVersion:1,records:{[destinationId]:{canonical:{state:'not-started'},views:{}}}}};
  await f.save();
  const history = await appendDecision({projectsRoot:f.context.projectsRoot,entry:{...f.event,id:uuid7(),operation_id:uuid7(),action:'note.recorded'}});
  const paths = [f.input.operationPath,baselinePath,history.file,f.file,currentPath];
  let before = await Promise.all(paths.map(filename => readFile(filename)));
  const disjoint = await preparePlanning({...f.input,dryRun:true});
  assert.equal(disjoint.status,'prepared');
  assert.equal(disjoint.recovery.operations[0].status,'scoped');
  assert.deepEqual(disjoint.recovery.suspendedRecordIds,[destinationId]);
  assert.ok(!disjoint.review.available.some(row => row.id === destinationId));
  assert.deepEqual(await Promise.all(paths.map(filename => readFile(filename))),before);
  f.operation.protectedFiles = [{path:currentPath,sha256:hash(await readFile(currentPath))}];
  await f.save();
  before = await Promise.all(paths.map(filename => readFile(filename)));
  const overlap = await preparePlanning({...f.input,dryRun:true});
  assert.equal(overlap.status,'recovery-required');
  assert.equal(overlap.recovery.operations[0].status,'blocking');
  assert.ok(overlap.recovery.operations[0].paths.includes(currentPath));
  assert.deepEqual(await Promise.all(paths.map(filename => readFile(filename))),before);
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

