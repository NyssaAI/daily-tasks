import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { resolveContext, planningBinding, assertPlanningScope } from '../lib/profile/context.mjs';
import { validateProfile } from '../lib/profile/profile.mjs';

const profile = {schema_version:1,user:{name:'Example',email:'owner@example.test'},timezone:'system',priorities:[],vaultRoot:'.',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans',templates:{task:'~/templates/task.md'},projectIndex:{ttlSeconds:14400}};
test('portable profile validates and resolves vault profile before home without subprocess cwd', async () => {
  assert.equal(validateProfile(profile).valid,true);
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/context-')));
  const vault = path.join(root,'vault'), home = path.join(root,'home');
  for (const dir of [vault,home]) await mkdir(path.join(dir,'.nyssaai/daily-tasks'),{recursive:true});
  await writeFile(path.join(home,'.nyssaai/daily-tasks/profile.json'),JSON.stringify({...profile,user:{name:'Home',email:'home@example.test'}}));
  await writeFile(path.join(vault,'.nyssaai/daily-tasks/profile.json'),JSON.stringify(profile));
  const result = await resolveContext({initialCwd:vault,homeRoot:home,now:'2026-10-06T14:00:00Z'});
  assert.equal(result.profile.user.email,'owner@example.test');
  assert.equal(result.projectsRoot,path.join(vault,'1-projects'));
  assert.equal(result.templates.task,path.join(home,'templates/task.md'));
  assert.equal(result.stateRoot,path.join(vault,'.nyssaai/daily-tasks'));
  assert.equal(result.localDate,'2026.10.06');
  assert.ok(result.timezone !== 'system');
  assert.equal((await resolveContext({vaultRoot:home,homeRoot:home})).profile.user.email,'home@example.test');
  await assert.rejects(resolveContext({homeRoot:home}),/vaultRoot|initialCwd/);
});

test('invalid portable traversal, TTL and malformed discovered profile are diagnosed', async () => {
  assert.equal(validateProfile({...profile,projectsRoot:'./../outside'}).valid,false);
  assert.equal(validateProfile({...profile,projectIndex:{ttlSeconds:-1}}).valid,false);
  await mkdir('.temp',{recursive:true});
  const vault = await mkdtemp(path.resolve('.temp/bad-profile-'));
  await mkdir(path.join(vault,'.nyssaai/daily-tasks'),{recursive:true});
  await writeFile(path.join(vault,'.nyssaai/daily-tasks/profile.json'),'{broken');
  await assert.rejects(resolveContext({vaultRoot:vault,homeRoot:vault}),/JSON/);
});

test('Windows vault bindings tolerate case differences and state containment stays safe', {skip:process.platform !== 'win32'}, async () => {
  await mkdir('.temp',{recursive:true});
  const vault = await realpath(await mkdtemp(path.resolve('.temp/context-case-')));
  const configRoot = path.join(vault,'.nyssaai/daily-tasks');
  await mkdir(configRoot,{recursive:true});
  await writeFile(path.join(configRoot,'profile.json'),JSON.stringify({...profile,vaultRoot:vault.toLowerCase()}));
  assert.equal((await resolveContext({vaultRoot:vault.toUpperCase(),homeRoot:vault})).configured,true);
  await writeFile(path.join(configRoot,'profile.json'),JSON.stringify({...profile,dailyPlansRelative:'.nyssaai/daily-tasks/output'}));
  await assert.rejects(resolveContext({vaultRoot:vault.toUpperCase(),homeRoot:vault}),/beneath configuration\/state/);
});

test('one home profile shares preferences while two vaults retain independent planning and state roots', async () => {
  const root = await realpath(await mkdtemp(path.resolve('.temp/two-vaults-')));
  const homeRoot = path.join(root,'home');
  await mkdir(path.join(homeRoot,'.nyssaai/daily-tasks'),{recursive:true});
  await writeFile(path.join(homeRoot,'.nyssaai/daily-tasks/profile.json'),JSON.stringify(profile));
  const contexts = [];
  for (const name of ['personal','work']) {
    const vaultRoot = path.join(root,name);
    await mkdir(vaultRoot);
    contexts.push(await resolveContext({vaultRoot,homeRoot}));
  }
  assert.equal(contexts[0].configRoot,contexts[1].configRoot);
  assert.notEqual(contexts[0].stateRoot,contexts[1].stateRoot);
  assert.notEqual(contexts[0].dailyPlansRoot,contexts[1].dailyPlansRoot);
  assert.notEqual(contexts[0].projectsRoot,contexts[1].projectsRoot);
  assert.notEqual(contexts[0].planningBinding,contexts[1].planningBinding);
  const first = {...contexts[0],contextBinding:contexts[0].planningBinding};
  assert.doesNotThrow(() => assertPlanningScope(first));
  assert.throws(() => assertPlanningScope({...first,dailyPlansRoot:contexts[1].dailyPlansRoot}),/roots differ/);
  assert.throws(() => planningBinding({...first,vaultRoot:[contexts[0].vaultRoot,contexts[1].vaultRoot]}),/one absolute root/);
  const wrongProfile = path.join(contexts[0].vaultRoot,'profile.json');
  await writeFile(wrongProfile,JSON.stringify({...profile,vaultRoot:contexts[0].vaultRoot}));
  await assert.rejects(resolveContext({vaultRoot:contexts[1].vaultRoot,homeRoot,profilePath:wrongProfile}),/vaultRoot conflicts/);
});
