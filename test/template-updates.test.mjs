import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, mkdir, writeFile, readFile, access, unlink, readdir } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { pathToFileURL } from 'node:url';
import { prepareTemplates, saveTemplateState } from '#core/templates/templates.mjs';
import { templateFingerprint } from '#core/templates/catalog.mjs';
import { resolveContext } from '#core/profile/context.mjs';

const kinds = ['dailyPlan','planDayReview','projectIndex','milestone','task'];
function catalog(version) {
  return Object.fromEntries(kinds.map(kind => {
    const content = `# ${kind}\n\n${version === 1 ? '- [ ] Old work' : '| Status | Task |\n| --- | --- |\n| [ ] | New work |'}\n`;
    return [kind,{kind,content,revision:templateFingerprint(content),contract:`${kind}-v1`,source:'bundled',history:[]}];
  }));
}
async function fixture() {
  await mkdir('.temp',{recursive:true});
  const directory = await mkdtemp(path.resolve('.temp/template-updates-'));
  const homeRoot = path.join(directory,'home'), vaultRoot = path.join(directory,'vault');
  const config = path.join(vaultRoot,'.nyssa-ai/daily-tasks');
  await mkdir(config,{recursive:true});
  await mkdir(homeRoot,{recursive:true});
  await mkdir(path.join(vaultRoot,'projects'));
  const profilePath = path.join(config,'profile.json');
  const profile = {schema_version:2,user:{name:'Example',email:'owner@example.test'},timezone:'UTC',projectsRoot:'./projects'};
  await writeFile(profilePath,JSON.stringify(profile));
  return {directory,profilePath,profile,config,input:{vaultRoot,homeRoot,kinds:['dailyPlan']}};
}
async function save(input, packet, action = 'baseline', decisions, options = {}) {
  return saveTemplateState({...input,action,expectedToken:packet.token,...(decisions ? {decisions,originalWords:'Synthetic explicit template choice'} : {})},options);
}

test('shared home template storage preserves personal ownership and one saved choice', async () => {
  const {input,profilePath} = await fixture();
  const request = {...input,homeRoot:input.vaultRoot,scope:'user'};
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const initial = await prepareTemplates(request,old);
  assert.equal(initial.sharedScopes.length,1);
  assert.equal(initial.storage.user.path,initial.storage.project.path);
  await save(request,initial,'baseline',undefined,old);
  const prepared = await prepareTemplates(request,next);
  assert.equal(prepared.templates.dailyPlan.activeScope,'user');
  const profileBefore = await readFile(profilePath,'utf8');
  const projectFiles = await readdir(path.join(input.vaultRoot,'projects'),{recursive:true});
  await save(request,prepared,'decide',[{kind:'dailyPlan',action:'accept'}],next);
  const again = await prepareTemplates(request,next);
  assert.equal(again.templates.dailyPlan.active.content,next.catalog.dailyPlan.content);
  assert.equal((await save(request,prepared,'decide',[{kind:'dailyPlan',action:'accept'}],next)).status,'unchanged');
  assert.equal(await readFile(profilePath,'utf8'),profileBefore);
  assert.deepEqual(await readdir(path.join(input.vaultRoot,'projects'),{recursive:true}),projectFiles);
});

test('template updates preserve observed layout across releases and remember revision-specific declines', async () => {
  const {input} = await fixture();
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const initial = await prepareTemplates(input,old);
  assert.equal(initial.templates.dailyPlan.shouldOffer,false);
  assert.equal(initial.templates.dailyPlan.origin,'observed');
  await save(input,initial,'baseline',undefined,old);
  const updated = await prepareTemplates(input,next);
  assert.equal(updated.templates.dailyPlan.shouldOffer,true);
  assert.equal(updated.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  await save(input,updated,'decide',[{kind:'dailyPlan',action:'decline'}],next);
  const declined = await prepareTemplates(input,next);
  assert.equal(declined.templates.dailyPlan.shouldOffer,false);
  assert.equal(declined.templates.dailyPlan.policy,'ask');
  assert.equal(declined.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  assert.equal((await prepareTemplates({...input,review:true},next)).templates.dailyPlan.shouldOffer,true);
  assert.equal((await prepareTemplates(input,{catalog:{...next.catalog,dailyPlan:{...next.catalog.dailyPlan,content:'# Another layout\n',revision:templateFingerprint('# Another layout\n')}}})).templates.dailyPlan.shouldOffer,true);
});

test('acceptance is atomic, repeatable, scoped to requested kinds, and never writes existing Markdown', async () => {
  const {input} = await fixture();
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const request = {...input,kinds:['dailyPlan','planDayReview']};
  await save(request,await prepareTemplates(request,old),'baseline',undefined,old);
  const filename = path.join(input.vaultRoot,'today.md');
  await writeFile(filename,'Existing personal notes and selections.\n');
  const before = await prepareTemplates(request,next);
  const decisions = [{kind:'dailyPlan',action:'accept'},{kind:'planDayReview',action:'decline'}];
  const result = await save(request,before,'decide',decisions,next);
  assert.equal(result.status,'saved');
  assert.equal((await save(request,before,'decide',decisions,next)).status,'unchanged');
  const after = await prepareTemplates(request,next);
  assert.equal(after.templates.dailyPlan.active.content,next.catalog.dailyPlan.content);
  assert.equal(after.templates.planDayReview.active.content,old.catalog.planDayReview.content);
  assert.equal(await readFile(filename,'utf8'),'Existing personal notes and selections.\n');
  assert.equal(after.templates.dailyPlan.origin,'accepted');
  assert.equal(after.templates.dailyPlan.policy,'ask');
});

test('latest and keep policies are explicit per-kind preferences; postponement preserves ask', async () => {
  const {input} = await fixture();
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const request = {...input,kinds};
  await save(request,await prepareTemplates(request,old),'baseline',undefined,old);
  await save(request,await prepareTemplates(request,old),'decide',[
    {kind:'dailyPlan',action:'set-policy',policy:'latest'},
    {kind:'task',action:'set-policy',policy:'keep'},
  ],old);
  const upgraded = await prepareTemplates(request,next);
  assert.equal(upgraded.templates.dailyPlan.active.content,next.catalog.dailyPlan.content);
  assert.equal(upgraded.templates.dailyPlan.shouldOffer,false);
  assert.equal(upgraded.templates.task.active.content,old.catalog.task.content);
  assert.equal(upgraded.templates.task.shouldOffer,false);
  assert.equal(upgraded.templates.milestone.shouldOffer,true);
  await save(request,upgraded,'decide',[{kind:'milestone',action:'postpone'}],next);
  const postponed = await prepareTemplates(request,next);
  assert.equal(postponed.templates.milestone.active.content,old.catalog.milestone.content);
  assert.equal(postponed.templates.milestone.policy,'ask');
  assert.equal(postponed.templates.milestone.shouldOffer,true);
});

test('custom templates remain intact and block unattended replacement even under latest', async () => {
  const {input,profile,profilePath} = await fixture();
  const customPath = path.join(input.vaultRoot,'custom.md');
  const content = '# My own layout\n\n- [ ] Work\n';
  await writeFile(customPath,content);
  await writeFile(profilePath,JSON.stringify({...profile,templates:{dailyPlan:'./custom.md'}}));
  const options = {catalog:catalog(2)};
  const before = await prepareTemplates(input,options);
  assert.equal(before.templates.dailyPlan.active.source,'custom');
  await save(input,before,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'latest'}],options);
  const checked = await prepareTemplates(input,options);
  assert.equal(checked.templates.dailyPlan.active.content,content);
  assert.equal(checked.templates.dailyPlan.automaticBlocked,true);
  await save(input,checked,'decide',[{kind:'dailyPlan',action:'accept'}],options);
  assert.equal((await prepareTemplates(input,options)).templates.dailyPlan.fileUpdate.status,'pending');
  assert.equal(await readFile(customPath,'utf8'),content);
  // The skill writes the approved file; only then can the runtime complete the choice.
  await writeFile(customPath,options.catalog.dailyPlan.content);
  await save(input,await prepareTemplates(input,options),'baseline',undefined,options);
  // A user's subsequent edit remains visible and does not erase their lasting preference.
  await writeFile(customPath,content+'A new personal note.\n');
  const edited = await prepareTemplates(input,options);
  assert.match(edited.templates.dailyPlan.active.content,/personal note/);
  await save(input,edited,'baseline',undefined,options);
  const retainedEdit = await prepareTemplates(input,options);
  assert.equal(retainedEdit.templates.dailyPlan.policy,'latest');
  assert.equal(retainedEdit.templates.dailyPlan.shouldOffer,false);
});

test('unchanged template content across plugin releases causes no offer or repeated baseline write', async () => {
  const {input,config} = await fixture();
  const old = {catalog:catalog(1)};
  await save(input,await prepareTemplates(input,old),'baseline',undefined,old);
  const filename = path.join(config,'templates/updates.json');
  const before = await readFile(filename,'utf8');
  const codeOnly = {catalog:Object.fromEntries(Object.entries(catalog(1)).map(([kind,value]) => [kind,{...value,pluginVersion:'99.0.0'}]))};
  const next = await prepareTemplates(input,codeOnly);
  assert.equal(next.templates.dailyPlan.shouldOffer,false);
  assert.equal((await save(input,next,'baseline',undefined,codeOnly)).status,'unchanged');
  assert.equal(await readFile(filename,'utf8'),before);
});

test('resetting a deliberate project choice restores personal policy and retained content', async () => {
  const {input,profile} = await fixture();
  const userConfig = path.join(input.homeRoot,'.nyssa-ai/daily-tasks');
  await mkdir(userConfig,{recursive:true});
  await writeFile(path.join(userConfig,'profile.json'),JSON.stringify({schema_version:2,user:profile.user}));
  const personal = {homeRoot:input.homeRoot,kinds:['dailyPlan'],scope:'user'};
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  await save(personal,await prepareTemplates(personal,old),'decide',[{kind:'dailyPlan',action:'set-policy',policy:'keep'}],old);
  await save(input,await prepareTemplates(input,next),'decide',[{kind:'dailyPlan',action:'accept'}],next);
  assert.equal((await prepareTemplates(input,next)).templates.dailyPlan.active.content,next.catalog.dailyPlan.content);
  await save(input,await prepareTemplates(input,next),'decide',[{kind:'dailyPlan',action:'reset'}],next);
  const restored = await prepareTemplates(input,next);
  assert.equal(restored.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  assert.equal(restored.templates.dailyPlan.policy,'keep');
  assert.equal(restored.templates.dailyPlan.activeScope,'user');
});

test('personal choices inherit into vaults, project resets mask them, and configuration is not vault state', async () => {
  const {input,profilePath,profile,config} = await fixture();
  const userConfig = path.join(input.homeRoot,'.nyssa-ai/daily-tasks');
  await mkdir(userConfig,{recursive:true});
  await writeFile(path.join(userConfig,'profile.json'),JSON.stringify({schema_version:2,user:profile.user}));
  const personal = {homeRoot:input.homeRoot,kinds:['dailyPlan'],scope:'user'};
  const old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  await save(personal,await prepareTemplates(personal,old),'baseline',undefined,old);
  assert.equal((await prepareTemplates(input,next)).templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  await save(personal,await prepareTemplates(personal,next),'decide',[{kind:'dailyPlan',action:'accept'}],next);
  assert.equal((await prepareTemplates(input,next)).templates.dailyPlan.origin,'accepted');
  await writeFile(profilePath,JSON.stringify({...profile,templates:{dailyPlan:null}}));
  const reset = await prepareTemplates(input,next);
  assert.equal(reset.templates.dailyPlan.origin,'observed');
  await save(input,reset,'baseline',undefined,next);
  assert.equal((await resolveContext(input)).stateRoot,path.join(input.vaultRoot,'.nyssa-ai/daily-tasks'));
  assert.equal(await readFile(profilePath,'utf8'),JSON.stringify({...profile,templates:{dailyPlan:null}}));
  await access(path.join(config,'templates/updates.json'));
});

test('changed sources reject stale choices and dry runs create no template store', async () => {
  const {input,config} = await fixture();
  const options = {catalog:catalog(1)};
  const before = await prepareTemplates(input,options);
  assert.equal((await saveTemplateState({...input,action:'baseline',expectedToken:before.token,dryRun:true},options)).status,'preview');
  await assert.rejects(access(path.join(config,'templates/updates.json')),{code:'ENOENT'});
  await save(input,before,'baseline',undefined,options);
  await assert.rejects(save(input,before,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'keep'}],options),/changed/);
});

test('an interrupted project log effect remains recoverable with the same event', async () => {
  const {input} = await fixture();
  const options = {catalog:catalog(1)};
  const prepared = await prepareTemplates(input,options);
  const logDirectory = path.join(input.vaultRoot,'projects/.daily-tasks');
  await mkdir(logDirectory,{recursive:true});
  // Multiple active decision files prevent the second effect, after the choice checkpoint is saved.
  const active1 = path.join(logDirectory,'2026.10.11-decisions.json');
  const active2 = path.join(logDirectory,'2026.10.12-decisions.json');
  await writeFile(active1,'');
  await writeFile(active2,'');
  const decisions = [{kind:'dailyPlan',action:'set-policy',policy:'keep'}];
  await assert.rejects(save(input,prepared,'decide',decisions,options),/Multiple active decision files/);
  const interrupted = await prepareTemplates(input,options);
  assert.equal(interrupted.status,'recovery-required');
  assert.deepEqual(interrupted.pendingScopes,['project']);
  await unlink(active1);
  await unlink(active2);
  await save(input,interrupted,'recover',undefined,options);
  await save(input,prepared,'decide',decisions,options);
  const logFiles = (await readdir(logDirectory)).filter(name => name.endsWith('.json'));
  const lines = (await readFile(path.join(logDirectory,logFiles[0]),'utf8')).trim().split('\n').map(line => JSON.parse(line));
  assert.equal(lines.length,1);
  assert.equal(lines[0].action,'templates.changed');
  assert.equal((await prepareTemplates(input,options)).status,'prepared');
});

test('live and malformed template locks are preserved by both writes and recovery', async () => {
  const {input,config} = await fixture();
  const options = {catalog:catalog(1)};
  const prepared = await prepareTemplates(input,options);
  await mkdir(path.join(config,'templates'),{recursive:true});
  const filename = path.join(config,'templates/.updates.lock');
  for (const owner of [JSON.stringify({pid:process.pid,id:'live-fixture'}), '{"pid":', '{}']) {
    await writeFile(filename,owner);
    for (const action of ['baseline','recover']) await assert.rejects(save(input,prepared,action,undefined,options),/never removed automatically/);
    assert.equal(await readFile(filename,'utf8'),owner);
    await assert.rejects(access(path.join(config,'templates/updates.json')),{code:'ENOENT'});
  }
});

test('interrupted acquisition publishes a complete owner; competing recoveries cannot remove its lock', async () => {
  const {input,config} = await fixture();
  const options = {catalog:catalog(1)};
  const storePath = path.join(config,'templates/updates.json');
  const storageModule = pathToFileURL(path.resolve('src/core/templates/storage.mjs')).href;
  const child = spawnSync(process.execPath,['--input-type=module','-e',
    `import {withTemplateLock} from ${JSON.stringify(storageModule)}; await withTemplateLock({path:process.argv[1]},async () => process.exit(29));`,storePath],{encoding:'utf8'});
  assert.equal(child.status,29,child.stderr);
  const filename = path.join(config,'templates/.updates.lock');
  const lock = await readFile(filename,'utf8');
  assert.equal(JSON.parse(lock).pid,child.pid);
  assert.match(JSON.parse(lock).id,/^[a-f0-9-]{36}$/);
  const prepared = await prepareTemplates(input,options);
  const attempts = await Promise.allSettled([save(input,prepared,'recover',undefined,options),save(input,prepared,'recover',undefined,options)]);
  assert.ok(attempts.every(result => result.status === 'rejected' && /never removed automatically/.test(result.reason.message)));
  assert.equal(await readFile(filename,'utf8'),lock);
  // The fixture owner has exited and both recovery attempts ended: deliberate removal is now safe.
  await unlink(filename);
  assert.equal((await save(input,prepared,'recover',undefined,options)).status,'recovered');
  assert.deepEqual(await readdir(path.dirname(storePath)),[]);
});

test('retained snapshots survive deleted source installations and incompatible latest updates need review', async () => {
  const {input,profile,profilePath} = await fixture();
  const source = path.join(input.vaultRoot,'previous-install.md');
  const old = {catalog:catalog(1)};
  await writeFile(source,old.catalog.dailyPlan.content);
  await writeFile(profilePath,JSON.stringify({...profile,templates:{dailyPlan:source}}));
  await save(input,await prepareTemplates(input,old),'decide',[{kind:'dailyPlan',action:'set-policy',policy:'latest'}],old);
  await unlink(source);
  const next = catalog(2);
  next.dailyPlan.contract = 'dailyPlan-v2';
  const retained = await prepareTemplates(input,{catalog:next});
  assert.equal(retained.templates.dailyPlan.sourceUnavailable,true);
  assert.equal(retained.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  assert.equal(retained.templates.dailyPlan.automaticBlocked,true);
  assert.equal(retained.templates.dailyPlan.shouldOffer,true);
  assert.equal(retained.templates.dailyPlan.compatibility,'record-contract-changed');
});

test('custom configurationSources, source resets and one-off formatting retain their scope contracts', async () => {
  const {input,profile,profilePath} = await fixture();
  await writeFile(profilePath,JSON.stringify({...profile,schema_version:2,priorities:[],vaultRoot:'.',dailyPlansRelative:'plans'}));
  const request = {...input,configurationSources:{schemaVersion:1,user:{profilePath:null},project:{profilePath}}};
  const options = {catalog:catalog(1)};
  const projectScoped = await prepareTemplates(request,options);
  assert.equal(projectScoped.scope,'project');
  await save(request,projectScoped,'baseline',undefined,options);
  const once = {...request,preferenceOverrides:{templates:{dailyPlan:null}}};
  const transient = await prepareTemplates(once,options);
  assert.equal(transient.templates.dailyPlan.transient,true);
  await assert.rejects(save(once,transient,'baseline',undefined,options),/One-off/);
  assert.equal((await prepareTemplates(request,options)).templates.dailyPlan.origin,'observed');
});

test('CLI preparation exposes only requested templates, records baselines, and planning includes the two relevant layouts', async () => {
  const {input,config,directory} = await fixture();
  const filename = path.join(directory,'input.json');
  const entry = path.resolve('src/cli/daily-tasks.mjs');
  async function call(operation,value) {
    await writeFile(filename,JSON.stringify(value));
    const result = spawnSync(process.execPath,[entry,operation,'--input',filename],{cwd:directory,encoding:'utf8'});
    assert.equal(result.status,0,result.stderr);
    return JSON.parse(result.stdout);
  }
  const prepared = await call('template-prepare',input);
  assert.deepEqual(Object.keys(prepared.templates),['dailyPlan']);
  await call('template-state',{...input,expectedToken:prepared.token,action:'baseline'});
  const packet = await call('planning-prepare',input);
  assert.deepEqual(Object.keys(packet.templates.templates),['dailyPlan','planDayReview']);
  assert.equal(packet.templates.templates.dailyPlan.origin,'observed');
  assert.deepEqual((await readdir(path.join(config,'templates'))).sort(),['updates.json']);
});
