import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile } from 'node:fs/promises';
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
  const target = {id:'test-host',kind:'host',suite:'workflow-v2',platform:'win32/x64',configuration:'default',required:true};
  // Specify the documented contract independently of the verifier's scenario list.
  const requiredScenarios = ['acceptance','assignment-time','reconciliation','day-change','closure','configuration-discovery'];
  assert.deepEqual(scenarioIds,requiredScenarios);
  const result = {...target,target:target.id,runId:'synthetic-run',completed_at:'2026-10-05T19:00:00Z',candidate:{hash:'a'.repeat(64)},status:'pass',source_unchanged:true,hostVersion:'fixture-1',model:'fixture',discovery:{isolated:true,loadedSkills:['/fixture/skills/daily-tasks/SKILL.md'],...artifact},scenarios:requiredScenarios.map(id => ({id,status:'pass',...artifact}))};
  await verifyResult(result,dir,target);
  assert.equal(releaseReady([target],new Map([[target.id,result]]),'a'.repeat(64)),true);
  assert.equal(releaseReady([target],new Map(),'a'.repeat(64)),false);
  assert.equal(releaseReady([target],new Map([[target.id,result]]),'b'.repeat(64)),false);
  await assert.rejects(verifyResult({...result,scenarios:[]},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.filter(s => s.id !== 'configuration-discovery')},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.map((s,i) => i === 5 ? {...s,id:'closure'} : s)},dir,target),/Incomplete/);
  await assert.rejects(verifyResult({...result,scenarios:result.scenarios.map((s,i) => i ? s : {...s,status:'fail'})},dir,target),/False/);
  await assert.rejects(verifyResult({...result,discovery:{...result.discovery,isolated:false}},dir,target),/discovery/);
  await writeFile(path.join(dir,'observation.txt'),'changed');
  await assert.rejects(verifyResult(result,dir,target),/Evidence changed/);
});
