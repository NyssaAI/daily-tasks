import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, writeFile, realpath, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';
import { resolveContext, planningBinding, assertPlanningScope } from '../lib/profile/context.mjs';
import { validateProfile } from '../lib/profile/profile.mjs';
import { preparePlanning, savePlanningState } from '../lib/planning/session.mjs';
import { planningScreen } from './fixtures/planning-screen.mjs';
import { uuid7 } from '../lib/identity/identity.mjs';
import { verifiedMaintenanceStatus, inspectMaintenance } from '../lib/planning/maintenance.mjs';
import { verifyOperation } from '../lib/operations/verification.mjs';

const profile = {schema_version:1,user:{name:'Example',email:'owner@example.test'},timezone:'system',priorities:[],vaultRoot:'.',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans',templates:{task:'~/templates/task.md'},projectIndex:{ttlSeconds:14400}};
test('shared v2 sources project preferences without leaking bindings on reentry', async () => {
  await mkdir('.temp',{recursive:true});
  const homeRoot = await realpath(await mkdtemp(path.resolve('.temp/shared-profile-')));
  const conventional = path.join(homeRoot,'.nyssa-ai/daily-tasks/profile.json');
  await mkdir(path.dirname(conventional),{recursive:true});
  for (const profilePath of [conventional,path.join(homeRoot,'accepted-settings/custom.json')]) {
    await mkdir(path.dirname(profilePath),{recursive:true});
    const stored = {schema_version:2,user:profile.user,timezone:'UTC',vaultRoot:homeRoot,projectsRoot:'./projects',dailyPlansRelative:'daily'};
    await writeFile(profilePath,JSON.stringify(stored));
    const configurationSources = {schemaVersion:1,user:{profilePath},project:{profilePath}};
    const bound = await resolveContext({homeRoot,vaultRoot:homeRoot,configurationSources});
    assert.equal(bound.configured,true);
    assert.equal(bound.projectsRoot,path.join(homeRoot,'projects'));
    assert.deepEqual(bound.sharedScopes,[{scopes:['user','project'],directory:path.dirname(profilePath)}]);
    assert.deepEqual((await resolveContext({homeRoot,vaultRoot:homeRoot,configurationSources:bound.configurationSources})).profile,bound.profile);
    const userOnly = {...configurationSources,project:{profilePath:null}};
    const personal = await resolveContext({homeRoot,configurationSources:userOnly});
    assert.equal(personal.preferenceOnly,true);
    assert.equal(personal.profile.projectsRoot,undefined);
    const other = path.join(homeRoot,'other');
    const foreign = await resolveContext({homeRoot,vaultRoot:other,configurationSources:userOnly});
    assert.equal(foreign.configured,false,'A different workspace still needs its own project binding');
    assert.equal(foreign.profile.projectsRoot,undefined);
    await writeFile(profilePath,JSON.stringify({...stored,projectsRoot:'../unsafe'}));
    await assert.rejects(resolveContext({homeRoot,configurationSources:userOnly}),/invalid projectsRoot/);
    await writeFile(profilePath,JSON.stringify(stored));
  }
  assert.equal((await resolveContext({homeRoot,vaultRoot:homeRoot})).configured,true);
});
test('partial scoped preferences round-trip explicit sources and bundled resets without selecting another layer', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/layers-')));
  const homeRoot = path.join(root,'home'), vaultRoot = path.join(root,'vault');
  for (const directory of [homeRoot,vaultRoot]) await mkdir(path.join(directory,'.nyssa-ai/daily-tasks'),{recursive:true});
  const userPath = path.join(homeRoot,'.nyssa-ai/daily-tasks/profile.json');
  const projectPath = path.join(vaultRoot,'.nyssa-ai/daily-tasks/profile.json');
  await writeFile(userPath,JSON.stringify({schema_version:2,user:profile.user,timezone:'UTC',priorities:['personal'],templates:profile.templates,projectIndex:{ttlSeconds:1}}));
  await writeFile(projectPath,JSON.stringify({schema_version:2,projectsRoot:'./work',timezone:null,priorities:[],templates:{task:null},projectIndex:{ttlSeconds:null}}));
  const context = await resolveContext({vaultRoot,homeRoot});
  assert.equal(context.configured,true);
  assert.deepEqual(context.profile.priorities,[]);
  assert.deepEqual(context.templates,{});
  assert.equal(context.ttlSeconds,14400);
  assert.equal(context.projectsRoot,path.join(vaultRoot,'work'));
  const again = await resolveContext({vaultRoot,homeRoot,configurationSources:context.configurationSources,stateRoot:context.stateRoot});
  assert.deepEqual(again.configurationSources,context.configurationSources);
  assert.deepEqual(again.profile,context.profile);
  const overridden = await resolveContext({vaultRoot,homeRoot,configurationSources:context.configurationSources,preferenceOverrides:{timezone:'UTC',priorities:['only this request']}});
  assert.equal(overridden.timezone,'UTC');
  assert.deepEqual(overridden.profile.priorities,['only this request']);
  assert.equal(overridden.preferenceSources.timezone,'current-task');
  assert.deepEqual((await resolveContext({vaultRoot,homeRoot})).profile.priorities,[]);
  await assert.rejects(resolveContext({vaultRoot,homeRoot,configurationSources:context.configurationSources,profilePath:userPath}),/exclusive|simultaneous/);
  const personal = await resolveContext({homeRoot});
  assert.equal(personal.configured,true);
  assert.equal(personal.vaultRoot,undefined);
  assert.equal(personal.stateRoot,undefined);
  await assert.rejects(resolveContext({homeRoot,configurationSources:{schemaVersion:1,user:{profilePath:userPath},project:{profilePath:null}},preferenceOverrides:{projectsRoot:'./other'}}),/project binding/);
});

test('completed legacy state remains authoritative and divergent completed copies require reconciliation', async () => {
  await mkdir('.temp',{recursive:true});
  const vaultRoot = await realpath(await mkdtemp(path.resolve('.temp/completed-state-')));
  const canonical = path.join(vaultRoot,'.nyssa-ai/daily-tasks'), legacy = path.join(vaultRoot,'.nyssaai/daily-tasks');
  await mkdir(canonical,{recursive:true});
  await mkdir(path.join(legacy,'rollover'),{recursive:true});
  await writeFile(path.join(canonical,'profile.json'),JSON.stringify(profile));
  await writeFile(path.join(legacy,'rollover','2026.10.11.json'),JSON.stringify({completedAt:'2026-10-11T00:00:00Z',removedIds:['synthetic']}));
  const bound = await resolveContext({vaultRoot,homeRoot:vaultRoot});
  assert.equal(bound.stateRoot,legacy);
  const before = await readdir(vaultRoot,{recursive:true});
  for (const stateRoot of [canonical,path.join(vaultRoot,'custom-state')]) {
    await assert.rejects(resolveContext({vaultRoot,homeRoot:vaultRoot,stateRoot}),error =>
      /explicit.*state|state.*explicit/i.test(error.message) && error.message.includes(stateRoot) && error.message.includes(legacy));
  }
  assert.deepEqual(await readdir(vaultRoot,{recursive:true}),before);
  assert.equal((await resolveContext({vaultRoot,homeRoot:vaultRoot,stateRoot:legacy})).stateRoot,legacy);
  await mkdir(path.join(canonical,'rollover'));
  await writeFile(path.join(canonical,'rollover','2026.10.11.json'),JSON.stringify({completedAt:'2026-10-11T00:00:00Z',removedIds:['synthetic']}));
  assert.equal((await resolveContext({vaultRoot,homeRoot:vaultRoot})).stateRoot,canonical,'Identical authoritative copies use canonical precedence');
  assert.equal((await resolveContext({vaultRoot,homeRoot:vaultRoot,stateRoot:legacy})).stateRoot,legacy,'Identical copies preserve the explicit binding');
  await writeFile(path.join(canonical,'rollover','2026.10.11.json'),JSON.stringify({removedIds:[]}));
  await assert.rejects(resolveContext({vaultRoot,homeRoot:vaultRoot}),/reconciliation|conflicting.*state/i);
  await assert.rejects(resolveContext({vaultRoot,homeRoot:vaultRoot,
    configurationSources:bound.configurationSources,stateRoot:bound.stateRoot}),/reconciliation|conflicting.*state/i);
});

test('personal-only consumers require a vault without creating operational files', async () => {
  await mkdir('.temp',{recursive:true});
  const homeRoot = await realpath(await mkdtemp(path.resolve('.temp/personal-consumers-')));
  const settings = path.join(homeRoot,'.nyssa-ai/daily-tasks');
  await mkdir(settings,{recursive:true});
  const contents = JSON.stringify({schema_version:2,user:profile.user,timezone:'UTC'});
  await writeFile(path.join(settings,'profile.json'),contents);
  const before = await readdir(homeRoot,{recursive:true});
  assert.equal((await preparePlanning({homeRoot})).status,'setup-required');
  assert.equal((await verifiedMaintenanceStatus({homeRoot})).reason,'setup-required');
  await assert.rejects(inspectMaintenance({homeRoot}),/Configured vault context required/);
  await assert.rejects(verifyOperation({homeRoot}),/Configured vault context required/);
  assert.deepEqual(await readdir(homeRoot,{recursive:true}),before);
  assert.equal(await readFile(path.join(settings,'profile.json'),'utf8'),contents);
});

test('planning preparation preserves completed legacy rollover removals beneath canonical preferences', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/completed-planning-')));
  const vaultRoot = path.join(root,'vault'), homeRoot = path.join(root,'home');
  const canonical = path.join(vaultRoot,'.nyssa-ai/daily-tasks');
  const legacy = path.join(vaultRoot,'.nyssaai/daily-tasks');
  for (const directory of [homeRoot,canonical,path.join(legacy,'rollover'),path.join(vaultRoot,'projects'),path.join(vaultRoot,'daily')]) await mkdir(directory,{recursive:true});
  await writeFile(path.join(canonical,'profile.json'),JSON.stringify({...profile,timezone:'UTC',projectsRoot:'./projects',dailyPlansRelative:'daily'}));
  const planId = uuid7(), removedId = uuid7();
  await writeFile(path.join(vaultRoot,'daily/2026.10.11-daily-plan.md'),`---\nid: ${planId}\ntype: daily-plan\n---\n`);
  await writeFile(path.join(vaultRoot,'daily/2026.10.10-daily-plan.md'),`---\nid: ${uuid7()}\ntype: daily-plan\n---\n- [ ] Removed work <!-- ref:${removedId} -->\n`);
  const statePath = path.join(legacy,'rollover/2026.10.11.json');
  const state = JSON.stringify({schemaVersion:1,date:'2026.10.11',planId,operationId:uuid7(),completedAt:'2026-10-11T12:00:00Z',removedIds:[removedId]});
  await writeFile(statePath,state);
  const prepared = await preparePlanning({vaultRoot,homeRoot,now:'2026-10-11T14:00:00Z',dryRun:true});
  assert.equal(prepared.context.stateRoot,legacy);
  assert.equal(prepared.rollover.status,'complete');
  assert.deepEqual(prepared.rollover.selected,[]);
  assert.deepEqual(prepared.state.rollover.value.removedIds,[removedId]);
  assert.equal(await readFile(statePath,'utf8'),state);
});

test('existing scalar profiles cannot fall through, while unselected malformed legacy preferences are diagnostic only', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/scalar-profile-')));
  const homeRoot = path.join(root,'home'), vaultRoot = path.join(root,'vault');
  await mkdir(homeRoot);
  for (const folder of ['.nyssa-ai','.nyssaai']) await mkdir(path.join(vaultRoot,folder,'daily-tasks'),{recursive:true});
  const canonical = path.join(vaultRoot,'.nyssa-ai/daily-tasks/profile.json');
  const legacy = path.join(vaultRoot,'.nyssaai/daily-tasks/profile.json');
  await writeFile(legacy,JSON.stringify(profile));
  for (const value of ['null','false','0','[]']) {
    await writeFile(canonical,value);
    await assert.rejects(resolveContext({vaultRoot,homeRoot}),/Profile must be an object/);
  }
  await writeFile(canonical,JSON.stringify(profile));
  await writeFile(legacy,'{broken');
  const context = await resolveContext({vaultRoot,homeRoot});
  assert.equal(context.configured,true);
  assert.equal(context.profilePath,canonical);
  assert.equal(context.diagnostics[0].path,legacy);
});

test('schema-2 null markers are leaf-only, user bindings are rejected, and schema-1 validation remains strict', () => {
  for (const layer of [{user:null},{user:{name:null}},{templates:null},{projectIndex:null},{vaultRoot:null},{projectsRoot:null},{dailyPlansRelative:null},{templates:{unknown:null}}]) assert.equal(validateProfile({schema_version:2,...layer}).valid,false,JSON.stringify(layer));
  assert.equal(validateProfile({schema_version:2,timezone:null,priorities:null,templates:{task:null},projectIndex:{ttlSeconds:null}}).valid,true);
  assert.equal(validateProfile({...profile,templates:{task:null}}).valid,false);
});

test('frozen absence and custom source selections preserve scope after new conventional profiles appear', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/source-absence-')));
  const homeRoot = path.join(root,'home'), vaultRoot = path.join(root,'vault');
  for (const directory of [homeRoot,vaultRoot]) await mkdir(directory);
  const userPath = path.join(root,'custom-personal.json');
  await writeFile(userPath,JSON.stringify({schema_version:2,user:profile.user,timezone:'UTC'}));
  const configurationSources = {schemaVersion:1,user:{profilePath:userPath},project:{profilePath:null}};
  const personal = await resolveContext({vaultRoot,homeRoot,configurationSources});
  assert.equal(personal.configured,false,'Project collection is still required for vault work');
  await mkdir(path.join(vaultRoot,'.nyssa-ai/daily-tasks'),{recursive:true});
  await writeFile(path.join(vaultRoot,'.nyssa-ai/daily-tasks/profile.json'),JSON.stringify(profile));
  const frozen = await resolveContext({vaultRoot,homeRoot,configurationSources});
  assert.equal(frozen.configured,false);
  assert.deepEqual(frozen.configurationSources,configurationSources);
  assert.equal((await resolveContext({vaultRoot,homeRoot})).configured,true);
  await assert.rejects(resolveContext({vaultRoot:homeRoot,homeRoot,configurationSources:{...configurationSources,project:{profilePath:path.join(vaultRoot,'.nyssa-ai/daily-tasks/profile.json')}}}),/bound scope/);
});

test('preparation and saved review use the same custom personal and partial project layers from another cwd', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/layered-planning-')));
  const homeRoot = path.join(root,'home'), vaultRoot = path.join(root,'vault');
  for (const directory of [homeRoot,path.join(vaultRoot,'projects'),path.join(vaultRoot,'daily')]) await mkdir(directory,{recursive:true});
  const userPath = path.join(homeRoot,'accepted-settings/profile.json'), projectPath = path.join(vaultRoot,'accepted-settings/profile.json');
  for (const filename of [userPath,projectPath]) await mkdir(path.dirname(filename),{recursive:true});
  await writeFile(userPath,JSON.stringify({schema_version:2,user:profile.user,timezone:'UTC',templates:{task:'~/custom/task.md'}}));
  await writeFile(projectPath,JSON.stringify({schema_version:2,projectsRoot:'./projects',dailyPlansRelative:'daily',templates:{task:null}}));
  const configurationSources = {schemaVersion:1,user:{profilePath:userPath},project:{profilePath:projectPath}};
  await writeFile(path.join(vaultRoot,'daily','2026.10.11-daily-plan.md'),`---\nid: ${uuid7()}\ntype: daily-plan\n---\n`);
  const input = {vaultRoot,homeRoot,configurationSources,preferenceOverrides:{priorities:['session'],timezone:'America/New_York'},now:'2026-10-11T14:00:00Z'};
  const prepared = await preparePlanning(input);
  assert.equal(prepared.status,'prepared');
  assert.deepEqual(prepared.context.configurationSources,configurationSources);
  assert.deepEqual(prepared.context.templates,{});
  const bound = Object.fromEntries(['vaultRoot','homeRoot','configurationSources','preferenceOverrides','stateRoot','now'].map(key => [key,prepared.context[key]]));
  const saved = await savePlanningState({...bound,action:'save-review',reviewMarkdown:planningScreen(prepared),expectedPlanHash:prepared.current.sha256,
    expectedPreviousHash:null,expectedStateHash:null,expectedInventoryHash:prepared.inventoryHash,expectedReviewHash:prepared.reviewHash});
  assert.equal(saved.status,'saved');
  assert.equal(JSON.parse(await readFile(saved.path,'utf8')).mappingBinding,prepared.context.planningBinding);
  const reopened = await preparePlanning(bound);
  assert.deepEqual(reopened.context.configurationSources,configurationSources);
  assert.deepEqual(reopened.context.preferenceOverrides,input.preferenceOverrides);
  assert.deepEqual(reopened.context.profile.priorities,['session']);
  assert.equal(reopened.context.timezone,'America/New_York');
  assert.equal(reopened.state.review.path,saved.path);
});
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
  assert.equal(result.stateRoot,path.join(vault,'.nyssa-ai/daily-tasks'));
  assert.equal(result.localDate,'2026.10.06');
  assert.ok(result.timezone !== 'system');
  assert.equal((await resolveContext({vaultRoot:home,homeRoot:home})).profile.user.email,'home@example.test');
  assert.equal((await resolveContext({homeRoot:home})).preferenceOnly,true);
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
