import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile, readFile, copyFile } from 'node:fs/promises';
import { spawnSync } from 'node:child_process';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { verifyResult, releaseReady, scenarioIds } from '../evals/evidence.mjs';

test('evidence accepts complete host execution and rejects missing, corrupt and falsely passing results', async () => {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
  await mkdir(path.join(root,'.temp'),{recursive:true});
  const dir = await mkdtemp(path.join(root,'.temp','evidence-'));
  const body = 'synthetic verifier fixture, not native runtime evidence';
  await writeFile(path.join(dir,'observation.txt'),body);
  const artifact = {output:'observation.txt',sha256:createHash('sha256').update(body).digest('hex')};
  const target = {id:'test-host',kind:'host',suite:'workflow-v3',platform:'win32/x64',configuration:'default',required:true};
  // Specify the documented contract independently of the verifier's scenario list.
  const requiredScenarios = ['acceptance','assignment-time','reconciliation','day-change','closure','configuration-discovery','milestone-workspace','workspace-migration'];
  assert.deepEqual(scenarioIds,requiredScenarios);
  const result = {...target,target:target.id,runId:'synthetic-run',completed_at:'2026-10-05T19:00:00Z',candidate:{hash:'a'.repeat(64)},status:'pass',source_unchanged:true,hostVersion:'fixture-1',model:'fixture',discovery:{isolated:true,loadedSkills:['/fixture/skills/daily-tasks/SKILL.md'],...artifact},scenarios:requiredScenarios.map(id => ({id,status:'pass',...artifact}))};
  await verifyResult(result,dir,target);
  await verifyResult({...result,suite:'workflow-v2',scenarios:result.scenarios.slice(0,6)},dir,{...target,suite:'workflow-v2'});
  await assert.rejects(verifyResult({...result,suite:'workflow-v2',scenarios:result.scenarios.slice(0,6)},dir,target),/Invalid result identity/);
  assert.equal(releaseReady([target],new Map([[target.id,result]]),'a'.repeat(64)),true);
  assert.equal(releaseReady([target],new Map(),'a'.repeat(64)),false);
  assert.equal(releaseReady([target],new Map([[target.id,result]]),'b'.repeat(64)),false);
  await assert.rejects(verifyResult({...result,scenarios:[]},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.slice(0,6)},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.filter(s => s.id !== 'configuration-discovery')},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.map((s,i) => i === 5 ? {...s,id:'closure'} : s)},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.map((s,i) => i ? s : {...s,status:'fail'})},dir,target),/False/);
  await assert.rejects(verifyResult({...result,discovery:{...result.discovery,isolated:false}},dir,target),/discovery/);
  await writeFile(path.join(dir,'observation.txt'),'changed');
  await assert.rejects(verifyResult(result,dir,target),/Evidence changed/);
});

test('report retains historical v2 evidence without promoting it over workflow-v3 acceptance', async () => {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)),'..');
  await mkdir(path.join(root,'.temp'),{recursive:true});
  const directory = await mkdtemp(path.join(root,'.temp','eval-report-'));
  await mkdir(path.join(directory,'evals/results'),{recursive:true});
  await mkdir(path.join(directory,'scripts'));
  for (const name of ['report.mjs','evidence.mjs']) await copyFile(path.join(root,'evals',name),path.join(directory,'evals',name));
  // Isolate the reporting boundary from the repository's real candidate inventory.
  await writeFile(path.join(directory,'scripts/assemble.mjs'),`export const root = ${JSON.stringify(directory)};`);
  await writeFile(path.join(directory,'evals/inventory.mjs'),`export async function inventory() { return {hash: '${'a'.repeat(64)}'}; }`);
  const target = {id:'codex',kind:'host',required:true,suite:'workflow-v3',platform:'win32/x64',configuration:'default',next:'Run native workspace evals.'};
  await writeFile(path.join(directory,'evals/matrix.json'),JSON.stringify({targets:[target]}));
  const body = 'Synthetic report fixture; not host acceptance.';
  const artifact = {output:'observation.txt',sha256:createHash('sha256').update(body).digest('hex')};
  async function receipt(runId,suite,scenarios,completed_at) {
    const run = path.join(directory,'evals/results',runId);
    await mkdir(run);
    await writeFile(path.join(run,'observation.txt'),body);
    await writeFile(path.join(run,'result.json'),JSON.stringify({target:target.id,kind:'host',platform:target.platform,
      configuration:target.configuration,suite,runId,completed_at,candidate:{hash:'a'.repeat(64)},status:'pass',source_unchanged:true,
      hostVersion:'fixture',model:'fixture',discovery:{isolated:true,loadedSkills:['fixture'],...artifact},
      scenarios:scenarios.map(id => ({id,status:'pass',...artifact}))}));
  }
  const runReport = mode => spawnSync(process.execPath,[path.join(directory,'evals/report.mjs'),mode],{cwd:directory,encoding:'utf8'});
  await receipt('newer-v2','workflow-v2',['acceptance','assignment-time','reconciliation','day-change','closure','configuration-discovery'],'2026-10-08T13:00:00Z');
  assert.equal(runReport('write').status,0);
  assert.match(await readFile(path.join(directory,'evals/LATEST.md'),'utf8'),/Not run \/ unverified/);
  assert.equal(runReport('release').status,1);
  await receipt('older-v3','workflow-v3',['acceptance','assignment-time','reconciliation','day-change','closure','configuration-discovery','milestone-workspace','workspace-migration'],'2026-10-08T12:00:00Z');
  assert.equal(runReport('write').status,0);
  const report = await readFile(path.join(directory,'evals/LATEST.md'),'utf8');
  assert.match(report,/older-v3/);
  assert.doesNotMatch(report,/newer-v2/);
  assert.equal(runReport('release').status,0);
  await writeFile(path.join(directory,'evals/results/newer-v2/observation.txt'),'tampered');
  assert.equal(runReport('write').status,1,'Historical evidence must still be verified');
});
