import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, readdir, symlink } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { uuid7, isUuid7 } from '../lib/identity/identity.mjs';
import { parseRecord, validateRecords, checkClosure } from '../lib/records/records.mjs';
import { carryForward, parseChecklist } from '../lib/planning/planning.mjs';
import { validateProfile } from '../lib/profile/profile.mjs';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const owner = 'user@example.com';
const time = '2026-10-05T16:30:00.000Z';
async function workspace() {
  await mkdir(path.join(root,'.temp'),{recursive:true});
  return mkdtemp(path.join(root,'.temp','integration-'));
}
function call(entry, operation, inputPath, ...flags) {
  const result = spawnSync(process.execPath,[entry,operation,...(inputPath ? ['--input',inputPath] : []),...flags],{encoding:'utf8',cwd:root});
  return {status:result.status,output:result.stdout.trim() ? JSON.parse(result.stdout) : null,error:result.stderr.trim() ? JSON.parse(result.stderr) : null};
}
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
test('profile validates explicit identity timezone and safe independently chosen roots', async () => {
  const directory = await workspace();
  const profile = {schema_version:1,user:{name:'Example',email:owner},timezone:'America/Chicago',priorities:[],vaultRoot:directory,projectsRoot:directory,dailyPlansRelative:'2-areas/daily-plans'};
  assert.equal(validateProfile(profile).valid,true);
  for (const change of [{timezone:'not-a-zone'},{projectsRoot:'relative'},{dailyPlansRelative:'../outside'},{user:{name:'Example'}}]) assert.equal(validateProfile({...profile,...change}).valid,false);
});
test('published templates become valid related records and gate milestone closure', async () => {
  const directory = await workspace();
  const replacements = {PROJECT_UUID:uuid7(),MILESTONE_UUID:uuid7(),TASK_UUID:uuid7(),DOD_UUID:uuid7(),CRITERION_UUID:uuid7(),BLOCKER_UUID:uuid7(),OWNER_EMAIL:owner,GMT_TIMESTAMP:time,PROJECT_TITLE:'Publish',MILESTONE_TITLE:'Release',TASK_TITLE:'Package',BLOCKER_TITLE:'Approval',MILESTONE_SLUG:'release',TASK_SLUG:'package',BLOCKER_SLUG:'approval'};
  const mapping = [['project-index.md','project-index.md'],['milestone.md','release/milestone.md'],['task.md','release/package.md'],['definition-of-done.md','release/definition-of-done.md'],['blocker.md','blockers/approval.md']];
  const records = [];
  for (const [template,relative] of mapping) {
    let markdown = await readFile(path.join(root,'skills/daily-tasks/assets',template),'utf8');
    for (const [key,value] of Object.entries(replacements)) markdown = markdown.replaceAll(key,value);
    if (template === 'task.md') markdown += `\n- [[../blockers/approval|Approval]] <!-- ref: ${replacements.BLOCKER_UUID} -->\n`;
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
