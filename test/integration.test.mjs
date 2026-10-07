import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, readdir, symlink, cp } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath, pathToFileURL } from 'node:url';
import { uuid7, isUuid7 } from '../lib/identity/identity.mjs';
import { parseRecord, validateRecords, checkClosure } from '../lib/records/records.mjs';
import { carryForward, parseChecklist } from '../lib/planning/planning.mjs';
import { validateProfile } from '../lib/profile/profile.mjs';
import { planningBinding } from '../lib/profile/context.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const owner = 'user@example.com';
const time = '2026-10-05T16:30:00.000Z';
async function workspace() {
  await mkdir(path.join(root,'.temp'),{recursive:true});
  return mkdtemp(path.join(root,'.temp','integration-'));
}
function callFrom(cwd, entry, operation, inputPath, ...flags) {
  const result = spawnSync(process.execPath,[entry,operation,...(inputPath ? ['--input',inputPath] : []),...flags],{encoding:'utf8',cwd});
  return {status:result.status,output:result.stdout.trim() ? JSON.parse(result.stdout) : null,error:result.stderr.trim() ? JSON.parse(result.stderr) : null};
}
const call = (entry,operation,inputPath,...flags) => callFrom(root,entry,operation,inputPath,...flags);
test('CLI accepts Windows UTF-8 BOM input and reports the package version', async () => {
  const directory = await workspace(), input = path.join(directory,'input.json');
  await writeFile(input,'\uFEFF' + JSON.stringify({time,timezone:'America/Chicago'}));
  const entry = path.join(root,'bin/daily-tasks.mjs');
  assert.equal(call(entry,'local-day',input).status,0);
  assert.equal(call(entry,'--help').output.version,JSON.parse(await readFile(path.join(root,'package.json'),'utf8')).version);
});
test('assembled packages and source hashes are identical for LF and CRLF source files', async () => {
  const directory = await workspace();
  for (const name of ['skills','lib','bin','plugin.json','LICENSE','package.json','capabilities.json']) {
    await cp(path.join(root,name),path.join(directory,name),{recursive:true});
  }
  await mkdir(path.join(directory,'scripts'));
  await cp(path.join(root,'scripts/assemble.mjs'),path.join(directory,'scripts/assemble.mjs'));
  const {buildPackages,tree} = await import(pathToFileURL(path.join(directory,'scripts/assemble.mjs')).href);
  const sources = await tree(directory);
  for (const [name,value] of sources) await writeFile(path.join(directory,name),value);
  const baseline = await buildPackages();
  for (const [name,value] of sources) await writeFile(path.join(directory,name),value.replaceAll('\n','\r\n'));
  assert.deepEqual(await buildPackages(),baseline);
});
test('UUIDv7 carries timestamp/version/variant without conflating identities', () => {
  const ids = Array.from({length:1000}, () => uuid7(1791217800000));
  assert.equal(new Set(ids).size,1000);
  assert.ok(ids.every(isUuid7));
  assert.equal(parseInt(ids[0].replaceAll('-','').slice(0,12),16),1791217800000);
});
test('carry-forward retains selected own/delegated work but not terminal or removed work', () => {
  const ids = Array.from({length:6}, () => uuid7());
  const records = ids.slice(0,5).map((id,index) => ({id,owner,state:['not-started','in-progress','completed','cancelled','not-started'][index],...(index === 1 ? {assignee:'research-agent'} : {})}));
  const rows = ids.map((id,index) => ({id,selected:index !== 4}));
  const next = carryForward(rows,records,owner);
  assert.deepEqual(next.own.map(row => row.id),[ids[0]]);
  assert.deepEqual(next.delegated.map(row => row.id),[ids[1]]);
  assert.equal(next.unresolved[0].reason,'missing-record');
  assert.equal(records[0].state,'not-started');
  const parsed = parseChecklist(`- [ ] New manual candidate\n- [x] [[task|Done]] <!-- ref: ${ids[0]} -->`);
  assert.equal(parsed[0].candidate,true);
  assert.equal(parsed[1].id,ids[0]);
});

test('inspection discovers uppercase Markdown and suggests a descriptive lowercase rename', async () => {
  const directory = await workspace();
  const taskId = uuid7(), projectId = uuid7(), milestoneId = uuid7();
  await writeFile(path.join(directory,'Task.MD'),`---\nid: ${taskId}\ntype: task\ntitle: Prepare budget\nowner: ${owner}\ntask-state: not-started\ncreated_at: ${time}\nupdated_at: ${time}\nproject_id: ${projectId}\nmilestone_id: ${milestoneId}\n---\n# Prepare budget\n`);
  const inputPath = path.join(directory,'input.json');
  await writeFile(inputPath,JSON.stringify({projectsRoot:directory}));
  const result = call(path.join(root,'bin/daily-tasks.mjs'),'inspect-records',inputPath);
  assert.equal(result.status,0);
  assert.equal(result.output.records[0].id,taskId);
  assert.equal(result.output.diagnostics.find(d => d.code === 'noncanonical-filename').suggestedFilename,'prepare-budget.md');
  assert.equal((await readdir(directory)).includes('Task.MD'),true);
});
test('profile validates explicit identity timezone and safe independently chosen roots', async () => {
  const directory = await workspace();
  const profile = {schema_version:1,user:{name:'Example',email:owner},timezone:'America/Chicago',priorities:[],vaultRoot:directory,projectsRoot:directory,dailyPlansRelative:'2-areas/daily-plans'};
  assert.equal(validateProfile(profile).valid,true);
  const systemProfile = validateProfile({...profile,timezone:'system'});
  assert.equal(systemProfile.valid,true);
  assert.equal(systemProfile.resolvedTimezone,Intl.DateTimeFormat().resolvedOptions().timeZone);
  assert.equal(validateProfile({...profile,templates:{projectIndex:path.join(directory,'project-example.md'),dailyPlan:path.join(directory,'day-example.md')}}).valid,true);
  for (const key of ['projectIndex','dailyPlan','milestone','task']) {
    assert.equal(validateProfile({...profile,templates:{[key]:path.join(directory,`${key}.md`)}}).valid,true);
    for (const filename of ['relative.md',42,path.join(directory,'example.txt')]) {
      assert.equal(validateProfile({...profile,templates:{[key]:filename}}).valid,false);
    }
  }
  for (const templates of [null, [], 'example.md', {dailyPlan:'relative.md'}, {projectIndex:42}, {unknown:path.join(directory,'example.md')}]) {
    assert.equal(validateProfile({...profile,templates}).valid,false);
  }
  for (const change of [{timezone:'not-a-zone'},{projectsRoot:'relative'},{dailyPlansRelative:'../outside'},{user:{name:'Example'}}]) assert.equal(validateProfile({...profile,...change}).valid,false);
});
test('published templates become valid related records and gate milestone closure', async () => {
  const directory = await workspace();
  const replacements = {PROJECT_UUID:uuid7(),MILESTONE_UUID:uuid7(),TASK_UUID:uuid7(),DOD_UUID:uuid7(),CRITERION_UUID:uuid7(),BLOCKER_UUID:uuid7(),OWNER_EMAIL:owner,GMT_TIMESTAMP:time,PROJECT_TITLE:'Publish',MILESTONE_TITLE:'Release',TASK_TITLE:'Package',BLOCKER_TITLE:'Approval',MILESTONE_SLUG:'release',TASK_SLUG:'package',BLOCKER_SLUG:'approval'};
  const mapping = [['project-index.md','project-index.md'],['milestone.md','release/milestone.md'],['task.md','release/package.md'],['definition-of-done.md','release/definition-of-done.md'],['blocker.md','blockers/approval.md']];
  const records = [];
  for (const [template,relative] of mapping) {
    let markdown = await readFile(path.join(root,'skills/daily-tasks/assets',template),'utf8');
    if (template === 'task.md') {
      // Optional dependencies are absent in this assignment.
      markdown = markdown.replace(/^## Depends on[\s\S]*?(?=## Required by)/m,'## Depends on\n\n')
        .replace(/^## Required by[\s\S]*?(?=## Blocked by)/m,'## Required by\n\n')
        .replace(/^> Provisional template.*\r?\n/m,'');
    }
    for (const [key,value] of Object.entries(replacements)) markdown = markdown.replaceAll(key,value);
    records.push(parseRecord(markdown,path.join(directory,relative)));
  }
  const diagnostics = validateRecords(records);
  assert.deepEqual(diagnostics,[]);
  assert.equal(checkClosure(replacements.MILESTONE_UUID,records).allowed,false);
  records.find(r => r.type === 'task').state = 'completed';
  records.find(r => r.type === 'dod').criteria[0].checked = true;
  records.find(r => r.type === 'blocker').state = 'resolved';
  const closure = checkClosure(replacements.MILESTONE_UUID,records);
  assert.equal(closure.allowed,true,JSON.stringify(closure.reasons));
});
test('CLI logs explicit acceptance, retries once, queries archive, rejects invalid input and previews without writes', async () => {
  const directory = await workspace();
  const entryPath = path.join(root,'bin/daily-tasks.mjs');
  const inputPath = path.join(directory,'input.json');
  const entry = {id:uuid7(),operation_id:uuid7(),action:'task.accepted',record_ids:[uuid7()],actor:{kind:'person',id:owner},activity_at:time,recorded_at:time,time_defaulted:false,original_words:'Accept all'};
  await writeFile(inputPath,JSON.stringify({projectsRoot:directory,entry}));
  const preview = call(entryPath,'log-append',inputPath,'--dry-run');
  assert.equal(preview.status,0,JSON.stringify(preview.error));
  assert.deepEqual(await readdir(directory),['input.json']);
  const append = call(entryPath,'log-append',inputPath);
  assert.equal(append.status,0,JSON.stringify(append.error));
  assert.equal(call(entryPath,'log-append',inputPath).output.duplicate,true);
  await writeFile(inputPath,JSON.stringify({projectsRoot:directory}));
  assert.equal(call(entryPath,'log-archive',inputPath).status,0);
  assert.equal(call(entryPath,'log-query',inputPath).output.entries.length,1);
  assert.equal(call(entryPath,'unknown',inputPath).status,1);
  assert.equal(call(entryPath,'log-query','relative.json').status,1);
});
test('assembled portable and Cowork CLI surfaces preserve operation behavior', async () => {
  const portable = call(path.join(root,'artifacts/portable/bin/daily-tasks.mjs'),'new-id');
  const cowork = call(path.join(root,'artifacts/cowork/scripts/daily-tasks.mjs'),'new-id');
  assert.equal(portable.status,0,JSON.stringify(portable.error));
  assert.equal(cowork.status,0,JSON.stringify(cowork.error));
  assert.ok(isUuid7(portable.output.id));
  assert.ok(isUuid7(cowork.output.id));
});

test('packaged rollover CLI merges a pre-created plan and preserves a later same-day removal', async () => {
  const directory = await workspace();
  const inputPath = path.join(directory,'rollover.json');
  const taskA = uuid7(), taskB = uuid7(), planId = uuid7();
  const roots = {vaultRoot:directory,projectsRoot:path.join(directory,'projects'),dailyPlansRoot:path.join(directory,'plans')};
  const input = {today:'2026.10.07',previousDate:'2026.10.06',planId,userEmail:owner,
    ...roots,contextBinding:planningBinding(roots),
    currentRows:[{id:taskB}],previousRows:[{id:taskA}],records:[{id:taskA,owner,state:'not-started'}]};
  for (const relative of ['artifacts/portable/bin/daily-tasks.mjs','artifacts/cowork/scripts/daily-tasks.mjs']) {
    const entry = path.join(root,relative);
    await writeFile(inputPath,JSON.stringify(input));
    const merged = callFrom(directory,entry,'plan-rollover',inputPath);
    assert.equal(merged.status,0,JSON.stringify(merged.error));
    assert.deepEqual(merged.output.selected.map(row => row.id),[taskB,taskA]);
    assert.equal(merged.output.own[0].carriedFrom,'2026.10.06');
    await writeFile(inputPath,JSON.stringify({...input,state:{schemaVersion:1,date:'2026.10.07',planId,
      operationId:uuid7(),completedAt:'2026-10-07T14:00:00Z'}}));
    const repeated = callFrom(directory,entry,'plan-rollover',inputPath);
    assert.equal(repeated.status,0,JSON.stringify(repeated.error));
    assert.equal(repeated.output.status,'complete');
    assert.deepEqual(repeated.output.selected.map(row => row.id),[taskB]);
  }
});

test('packaged planning CLI resolves portable scope independently of cwd and reuses inventory', async () => {
  const directory = await workspace();
  const unrelated = await workspace();
  const config = path.join(directory,'.nyssaai/daily-tasks');
  const project = path.join(directory,'1-projects/example');
  await mkdir(config,{recursive:true});
  await mkdir(path.join(project,'first'),{recursive:true});
  const projectId = uuid7(), milestoneId = uuid7(), taskId = uuid7();
  const doc = (id,type,title,extra='',body='') => `---\nid: ${id}\ntype: ${type}\ntitle: ${title}\nowner: ${owner}\n${type}-state: not-started\ncreated_at: ${time}\nupdated_at: ${time}\n${extra}---\n${body}\n`;
  await writeFile(path.join(project,'project-index.md'),doc(projectId,'project','Example','',`| Milestone | Task |\n| --- | --- |\n| [ ] [[first/milestone\\|First]] <!-- ref: ${milestoneId} --> | [ ] [[first/task\\|Task]] <!-- ref: ${taskId} --> |`));
  await writeFile(path.join(project,'first/milestone.md'),doc(milestoneId,'milestone','First',`project_id: ${projectId}\n`));
  await writeFile(path.join(project,'first/task.md'),doc(taskId,'task','Task',`project_id: ${projectId}\nmilestone_id: ${milestoneId}\n`));
  await writeFile(path.join(config,'profile.json'),JSON.stringify({schema_version:1,user:{name:'Example',email:owner},timezone:'system',priorities:[],vaultRoot:'.',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans',projectIndex:{ttlSeconds:14400}}));
  const inputPath = path.join(unrelated,'input.json');
  for (const relative of ['artifacts/portable/bin/daily-tasks.mjs','artifacts/cowork/scripts/daily-tasks.mjs']) {
    const entry = path.join(root,relative);
    await writeFile(inputPath,JSON.stringify({initialCwd:directory,now:time}));
    const context = callFrom(unrelated,entry,'resolve-context',inputPath);
    assert.equal(context.status,0,JSON.stringify(context.error));
    assert.equal(context.output.vaultRoot,directory);
    assert.equal(context.output.timezone,Intl.DateTimeFormat().resolvedOptions().timeZone);
    await writeFile(inputPath,JSON.stringify(context.output));
    const indexed = callFrom(unrelated,entry,'project-index',inputPath);
    assert.equal(indexed.status,0,JSON.stringify(indexed.error));
    assert.equal(indexed.output.inventory.tasks[0].id,taskId);
    const reused = callFrom(unrelated,entry,'project-index',inputPath);
    assert.equal(reused.output.status,'reused');
    assert.equal(reused.output.metrics.sourceReads,0);
    const scoped = {...context.output,contextBinding:context.output.planningBinding,inventoryBinding:reused.output.planningBinding};
    await writeFile(inputPath,JSON.stringify({...scoped,inventory:reused.output.inventory,userEmail:owner,timezone:context.output.timezone,now:time}));
    const view = callFrom(unrelated,entry,'planning-review',inputPath);
    assert.equal(view.status,0,JSON.stringify(view.error));
    assert.deepEqual(view.output.available.map(task => task.id),[taskId]);
    for (const mismatch of [{inventoryBinding:'0'.repeat(64)},
      {mapping:view.output.mapping,mappingBinding:'0'.repeat(64)}]) {
      await writeFile(inputPath,JSON.stringify({...scoped,inventory:reused.output.inventory,userEmail:owner,timezone:context.output.timezone,...mismatch}));
      const rejected = callFrom(unrelated,entry,'planning-review',inputPath);
      assert.equal(rejected.status,1);
      assert.match(rejected.error.error,/binding/);
    }
    await writeFile(inputPath,JSON.stringify({...scoped,inventory:reused.output.inventory,taskIds:[taskId],action:'add',date:'2026.10.08',today:'2026.10.05',dailyPlansRoot:context.output.dailyPlansRoot}));
    const selection = callFrom(unrelated,entry,'plan-selection',inputPath);
    assert.equal(selection.status,0,JSON.stringify(selection.error));
    assert.equal(selection.output.effects[0].to.createIfMissing,true);
    assert.equal(selection.output.conflicts.length,0);
  }
});

test('inspect-records scans nested records, skips hidden directories and rejects symlinks', async () => {
  const directory = await workspace();
  const projectsRoot = path.join(directory,'projects');
  const nested = path.join(projectsRoot,'nested');
  const hidden = path.join(projectsRoot,'.hidden');
  const outside = path.join(directory,'outside');
  for (const folder of [nested,hidden,outside]) await mkdir(folder,{recursive:true});
  const recordId = uuid7();
  const markdown = `---\ntype: project\ntitle: Scan fixture\nproject-state: not-started\nowner: ${owner}\ncreated_at: ${time}\nupdated_at: ${time}\n---\n<!-- id: ${recordId} -->\n`;
  await writeFile(path.join(nested,'project.md'),markdown);
  await writeFile(path.join(hidden,'ignored.md'),markdown);
  await writeFile(path.join(outside,'external.md'),markdown);
  await writeFile(path.join(projectsRoot,'ordinary.md'),'# Not a task record\n');
  const inputPath = path.join(directory,'input.json');
  const entryPath = path.join(root,'bin/daily-tasks.mjs');
  await writeFile(inputPath,JSON.stringify({projectsRoot}));
  const scan = call(entryPath,'inspect-records',inputPath);
  assert.equal(scan.status,0,JSON.stringify(scan.error));
  assert.deepEqual(scan.output.records.map(record => record.id),[recordId]);
  assert.deepEqual(scan.output.diagnostics,[]);
  await symlink(outside,path.join(projectsRoot,'external'),process.platform === 'win32' ? 'junction' : 'dir');
  const rejected = call(entryPath,'inspect-records',inputPath);
  assert.equal(rejected.status,1);
  assert.equal(rejected.output,null);
  assert.match(rejected.error.error,/Symbolic link excluded/);
});
