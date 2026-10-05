import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, realpath, readFile, readdir, rm, writeFile, mkdir, rename, symlink } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import path from 'node:path';
import { spawn } from 'node:child_process';
import { appendDecision, queryDecisions, archiveDecisions } from '../lib/log/decision-log.mjs';
import { uuid7 } from '../lib/identity/identity.mjs';
const makeEntry = (overrides = {}) => ({ id: uuid7(), operation_id: uuid7(), action: 'task.accepted', record_ids: [uuid7()], actor: {kind:'person',id:'user@example.test'}, activity_at:'2026-10-05T14:00:00Z', recorded_at:'2026-10-05T14:30:00Z', time_defaulted:false, ...overrides });
// macOS temporary paths can contain /var, a symlink; log roots must use the real directory.
async function fixture(t) { const root = await realpath(await mkdtemp(path.join(tmpdir(),'daily-log-'))); t.after(() => rm(root,{recursive:true,force:true})); return root; }
test('append, identical retry, conflicting retry, correction and archive preserve history', async t => {
 const projectsRoot = await fixture(t); const entry = makeEntry();
 const first = await appendDecision({projectsRoot,entry});
 assert.equal(first.duplicate,false);
 assert.equal((await appendDecision({projectsRoot,entry})).duplicate,true);
 await assert.rejects(appendDecision({projectsRoot,entry:{...entry,action:'other'}}), /operation/i);
 const bytes = await readFile(first.file,'utf8');
 const archived = await archiveDecisions({projectsRoot});
 assert.equal(await readFile(archived.file,'utf8'),bytes);
 const correction = makeEntry({corrects:entry.id});
 const second = await appendDecision({projectsRoot,entry:correction});
 assert.notEqual(second.file,first.file);
 assert.equal((await appendDecision({projectsRoot,entry})).duplicate,true);
 const result = await queryDecisions({projectsRoot,limit:1});
 assert.equal(result.total,2); assert.equal(result.entries.length,1); assert.equal(result.nextOffset,1);
 assert.equal((await queryDecisions({projectsRoot,offset:1})).entries[0].id,correction.id);
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry({corrects:uuid7()})}),/correct/i);
});
test('dry runs never create storage or modify existing bytes', async t => {
 const projectsRoot = await fixture(t); const entry = makeEntry();
 await appendDecision({projectsRoot,entry,dryRun:true});
 await archiveDecisions({projectsRoot,dryRun:true});
 assert.deepEqual(await readdir(projectsRoot),[]);
 const first = await appendDecision({projectsRoot,entry}); const bytes=await readFile(first.file,'utf8');
 await archiveDecisions({projectsRoot,dryRun:true}); await appendDecision({projectsRoot,entry:makeEntry(),dryRun:true});
 assert.equal(await readFile(first.file,'utf8'),bytes);
});
test('corrupt history and invalid input fail without rewriting history', async t => {
 const projectsRoot = await fixture(t);
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry({recorded_at:'2026-02-30T00:00:00Z'})}), /time|timestamp/i);
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry({actor:{kind:'person',id:''}})}), /actor/i);
 const first=await appendDecision({projectsRoot,entry:makeEntry()}); await writeFile(first.file,'{"truncated":');
 await assert.rejects(queryDecisions({projectsRoot}),/corrupt/i);
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry()}),/corrupt/i);
 assert.equal(await readFile(first.file,'utf8'),'{"truncated":');
});
test('person actors require email identity while named agents remain valid', async t => {
 const projectsRoot = await fixture(t);
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry({actor:{kind:'person',id:'Alex Example'}})}), /email/i);
 assert.deepEqual(await readdir(projectsRoot),[]);
 const result=await appendDecision({projectsRoot,entry:makeEntry({actor:{kind:'agent',id:'release-reviewer'}})});
 assert.equal(result.entry.actor.id,'release-reviewer');
});
test('separate processes serialize appends without losing entries', async t => {
 const projectsRoot=await fixture(t); const moduleUrl=new URL('../lib/log/decision-log.mjs',import.meta.url).href;
 await Promise.all(Array.from({length:8},()=>new Promise((resolve,reject)=>{
  const code=`import {appendDecision} from ${JSON.stringify(moduleUrl)}; await appendDecision(${JSON.stringify({projectsRoot,entry:makeEntry()})});`;
  const child=spawn(process.execPath,['--input-type=module','-e',code]); let errors=''; child.stderr.on('data',x=>errors+=x); child.on('error',reject); child.on('close',c=>c===0?resolve():reject(new Error(errors)));
 })));
 assert.equal((await queryDecisions({projectsRoot})).total,8);
});
test('same-day rotations choose fresh names and query filters include archives', async t => {
 const projectsRoot=await fixture(t); const record=uuid7(); const files=[];
 for(let i=0;i<3;i++){ const result=await appendDecision({projectsRoot,entry:makeEntry({record_ids:[record],action:i===0?'first':'later'})}); files.push(result.file); await archiveDecisions({projectsRoot}); }
 assert.equal(new Set(files).size,3);
 assert.equal((await queryDecisions({projectsRoot,recordId:record,action:'later'})).total,2);
 assert.equal((await queryDecisions({projectsRoot})).entries[0].action,'first');
 await assert.rejects(queryDecisions({projectsRoot,limit:1001}),/limit/i);
});
test('creation date is retained across days; archived IDs remain reserved', async t => {
 const projectsRoot=await fixture(t); const entry=makeEntry();
 const first=await appendDecision({projectsRoot,entry});
 const oldFile=path.join(path.dirname(first.file),'2020.01.01-decisions.json');
 await rename(first.file,oldFile);
 const next=await appendDecision({projectsRoot,entry:makeEntry()}); assert.equal(next.file,oldFile);
 await archiveDecisions({projectsRoot});
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry({id:entry.id})}),/ID already exists/i);
});
test('failed archive setup preserves original bytes and history', async t => {
 const projectsRoot=await fixture(t); const entry=makeEntry();
 const first=await appendDecision({projectsRoot,entry}); const bytes=await readFile(first.file,'utf8');
 const archiveDir=path.join(projectsRoot,'.daily-tasks','archives'); await writeFile(archiveDir,'obstruction');
 await assert.rejects(archiveDecisions({projectsRoot}),/directory/i);
 assert.equal(await readFile(first.file,'utf8'),bytes);
 await rm(archiveDir);
 assert.equal((await queryDecisions({projectsRoot})).total,1);
});
test('stale locks are reported without mutation or automatic breaking', async t => {
 const projectsRoot=await fixture(t); const lock=path.join(projectsRoot,'.daily-tasks','.decision-log.lock');
 await mkdir(lock,{recursive:true}); await writeFile(path.join(lock,'owner.json'),'prior process');
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry(),dryRun:true}),error=>error.code==='LOG_LOCKED' && error.message.includes(lock));
 assert.equal(await readFile(path.join(lock,'owner.json'),'utf8'),'prior process');
});
test('symlinked storage cannot redirect log operations', async t => {
 const projectsRoot=await fixture(t); const elsewhere=await fixture(t);
 await symlink(elsewhere,path.join(projectsRoot,'.daily-tasks'),process.platform==='win32'?'junction':'dir');
 await assert.rejects(appendDecision({projectsRoot,entry:makeEntry()}),error=>error.code==='UNSAFE_PATH');
 assert.deepEqual(await readdir(elsewhere),[]);
});
