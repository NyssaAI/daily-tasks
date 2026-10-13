import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { prepareTemplates, saveTemplateState } from '../lib/templates/templates.mjs';
import { templateFingerprint } from '../lib/templates/catalog.mjs';
import { queryDecisions } from '../lib/log/decision-log.mjs';

const kinds = ['dailyPlan','planDayReview','projectIndex','milestone','task'];
function catalog(version) {
  return Object.fromEntries(kinds.map(kind => {
    const content = `# ${kind}\n\nBundled layout ${version}\n`;
    return [kind,{kind,content,revision:templateFingerprint(content),contract:`${kind}-v1`,source:'bundled',history:[]}];
  }));
}
async function fixture(para = true) {
  await mkdir('.temp',{recursive:true});
  const root = await mkdtemp(path.resolve('.temp/template-lifecycle-'));
  const vaultRoot = path.join(root,'vault'), homeRoot = path.join(root,'home');
  const profilePath = path.join(vaultRoot,'.nyssa-ai/daily-tasks/profile.json');
  await mkdir(path.dirname(profilePath),{recursive:true});
  await mkdir(homeRoot);
  for (const name of para ? ['1-projects','2-areas','3-resources','4-archives'] : ['1-projects']) await mkdir(path.join(vaultRoot,name));
  const profile = {schema_version:2,user:{name:'Casey',email:'casey@example.test'},timezone:'UTC',projectsRoot:'./1-projects'};
  await writeFile(profilePath,JSON.stringify(profile));
  return {profile,profilePath,input:{vaultRoot,homeRoot,kinds:['dailyPlan'],now:'2026-10-13T15:00:00Z'}};
}
async function save(input,options,action='baseline',decisions) {
  const packet = await prepareTemplates(input,options);
  return saveTemplateState({...input,action,expectedToken:packet.token,...(decisions ? {decisions,originalWords:'Use the new daily plan layout'} : {})},options);
}
async function personalContext(f,templates) {
  const directory = path.join(f.input.homeRoot,'.nyssa-ai/daily-tasks');
  await mkdir(directory,{recursive:true});
  await writeFile(path.join(directory,'profile.json'),JSON.stringify({schema_version:2,user:f.profile.user,timezone:'UTC',templates}));
  return {homeRoot:f.input.homeRoot,kinds:['dailyPlan'],scope:'user',now:f.input.now};
}
async function materialize(f,options) {
  const packet = await prepareTemplates(f.input,options);
  const proposal = packet.placement.templates.dailyPlan;
  assert.equal(proposal.status,'create');
  await save(f.input,options);
  await mkdir(path.dirname(proposal.path),{recursive:true});
  // The skill owns Markdown and profile writes; the runtime only proposes them.
  await writeFile(proposal.path,proposal.content,{flag:'wx'});
  await writeFile(f.profilePath,JSON.stringify({...f.profile,templates:{dailyPlan:proposal.profileValue}}));
  await save(f.input,options);
  return proposal.path;
}

test('PARA template placement proposes visible files without writing or overwriting them', async () => {
  const f = await fixture(), options = {catalog:catalog(1)};
  const packet = await prepareTemplates({...f.input,kinds},options);
  assert.equal(packet.placement.status,'para');
  assert.equal(packet.placement.directory,path.join(f.input.vaultRoot,'3-resources/templates'));
  assert.equal(Object.keys(packet.placement.templates).length,5);
  const proposal = packet.placement.templates.dailyPlan;
  assert.equal(proposal.profileValue,'./3-resources/templates/daily-plan.md');
  await assert.rejects(readFile(proposal.path),{code:'ENOENT'});
  await mkdir(path.dirname(proposal.path));
  await writeFile(proposal.path,'Existing unrelated template');
  const conflict = await prepareTemplates(f.input,options);
  assert.equal(conflict.placement.templates.dailyPlan.status,'existing');
  assert.equal(await readFile(proposal.path,'utf8'),'Existing unrelated template');
});

test('non-PARA and ambiguous layouts create no placement proposal', async () => {
  const f = await fixture(false), options = {catalog:catalog(1)};
  assert.equal((await prepareTemplates(f.input,options)).placement.status,'not-para');
  for (const name of ['Areas','Resources','Archives','3-resources']) await mkdir(path.join(f.input.vaultRoot,name));
  assert.equal((await prepareTemplates(f.input,options)).placement.status,'ambiguous');
});

test('PARA placement follows an unnumbered Resources folder', async () => {
  const f = await fixture(false);
  for (const name of ['Areas','Resources','Archives']) await mkdir(path.join(f.input.vaultRoot,name));
  const packet = await prepareTemplates(f.input,{catalog:catalog(1)});
  assert.equal(packet.placement.directory,path.join(f.input.vaultRoot,'Resources/templates'));
});

test('exposing a retained bundled layout preserves its origin and choices across registration', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  await save(f.input,old,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'keep'}]);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  const filename = await materialize(f,next);
  const row = (await prepareTemplates(f.input,next)).templates.dailyPlan;
  assert.equal(await readFile(filename,'utf8'),old.catalog.dailyPlan.content);
  assert.equal(row.upstream.revision,old.catalog.dailyPlan.revision);
  assert.equal(row.policy,'keep');
  assert.equal(row.decisions[next.catalog.dailyPlan.revision],'declined');
  assert.equal(row.shouldOffer,false);
});

test('registering a personal retained layout preserves its choices after personal defaults change', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const personal = await personalContext(f);
  await save(personal,old,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'keep'}]);
  await save(personal,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  const filename = await materialize(f,next);
  await save(personal,next,'decide',[{kind:'dailyPlan',action:'accept'}]);
  const row = (await prepareTemplates(f.input,next)).templates.dailyPlan;
  assert.equal(row.active.content,old.catalog.dailyPlan.content);
  assert.equal(row.active.sourcePath,filename);
  assert.equal(row.policy,'keep');
  assert.equal(row.decisions[next.catalog.dailyPlan.revision],'declined');
  assert.equal(row.shouldOffer,false);
});

test('vault observation cannot duplicate a personal file approval or revive a canceled upgrade', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = path.join(f.input.homeRoot,'personal-plan-template.md');
  await writeFile(filename,old.catalog.dailyPlan.content);
  const personal = await personalContext(f,{dailyPlan:filename});
  await save(personal,old);
  await save(personal,next,'decide',[{kind:'dailyPlan',action:'accept'}]);
  const packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.baselineScope,'user');
  await assert.rejects(save(f.input,next),/owning user scope/);
  await assert.rejects(readFile(packet.storage.project.path),{code:'ENOENT'});
  await save({...f.input,scope:packet.templates.dailyPlan.baselineScope},next);
  await save(personal,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  const row = (await prepareTemplates(f.input,next)).templates.dailyPlan;
  assert.equal(row.fileUpdate,null);
  assert.equal(row.shouldOffer,false);
  assert.equal(row.active.content,old.catalog.dailyPlan.content);
});

test('older JSON-only adoption is recovered as a pending file update', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  const packet = await prepareTemplates(f.input,next);
  const storePath = packet.storage.project.path;
  const store = JSON.parse(await readFile(storePath,'utf8'));
  const entry = store.templates.dailyPlan;
  delete entry.upstream;
  entry.active = packet.templates.dailyPlan.available;
  entry.origin = 'accepted';
  entry.decisions[entry.active.revision] = 'accepted';
  await writeFile(storePath,JSON.stringify(store));
  const recovered = (await prepareTemplates(f.input,next)).templates.dailyPlan;
  assert.equal(recovered.active.content,old.catalog.dailyPlan.content);
  assert.equal(recovered.fileUpdate.status,'pending');
  assert.equal(recovered.fileUpdate.target.content,next.catalog.dailyPlan.content);
  assert.equal(recovered.shouldOffer,false);
  await writeFile(filename,recovered.fileUpdate.target.content);
  await save(f.input,next);
  assert.equal((await prepareTemplates(f.input,next)).templates.dailyPlan.fileUpdate,null);
});

test('visible templates pick up edits and retain their bundled origin for upgrade comparisons', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  const edited = old.catalog.dailyPlan.content+'\nMy weekly reflection\n';
  await writeFile(filename,edited);
  await save(f.input,old);
  const sameRelease = await prepareTemplates(f.input,old);
  assert.equal(sameRelease.templates.dailyPlan.active.content,edited);
  assert.equal(sameRelease.templates.dailyPlan.shouldOffer,false);
  const update = await prepareTemplates(f.input,next);
  const row = update.templates.dailyPlan;
  assert.equal(row.shouldOffer,true);
  assert.equal(row.upstream.content,old.catalog.dailyPlan.content);
  assert.equal(row.comparison.customized,true);
  assert.equal(row.active.sourcePath,filename);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'postpone'}]);
  assert.equal(await readFile(filename,'utf8'),edited);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  await writeFile(filename,edited+'Another personal edit\n');
  assert.equal((await prepareTemplates(f.input,next)).templates.dailyPlan.shouldOffer,false);
});

test('accepted file upgrades remain pending until actual Markdown is verified', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'accept'}]);
  let packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.fileUpdate.status,'pending');
  assert.equal(packet.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  assert.equal(await readFile(filename,'utf8'),old.catalog.dailyPlan.content);
  await writeFile(filename,'Unexpected edit');
  packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.fileUpdate.status,'conflict');
  await assert.rejects(save(f.input,next),/conflict/i);
  await writeFile(filename,next.catalog.dailyPlan.content);
  packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.fileUpdate.status,'applied');
  await save(f.input,next);
  const complete = await prepareTemplates(f.input,next);
  assert.equal(complete.templates.dailyPlan.fileUpdate,null);
  assert.equal(complete.templates.dailyPlan.active.content,next.catalog.dailyPlan.content);
  assert.equal(complete.templates.dailyPlan.upstream.revision,next.catalog.dailyPlan.revision);
  assert.equal(complete.templates.dailyPlan.shouldOffer,false);
});

test('explicit template pointers and bundled resets are preserved in PARA vaults', async () => {
  const f = await fixture(), options = {catalog:catalog(1)};
  const filename = path.join(f.input.homeRoot,'personal.md');
  await writeFile(filename,'# Personal layout\n');
  await writeFile(f.profilePath,JSON.stringify({...f.profile,templates:{dailyPlan:filename,task:null}}));
  const packet = await prepareTemplates({...f.input,kinds:['dailyPlan','task']},options);
  assert.equal(packet.placement.templates.dailyPlan.status,'configured');
  assert.equal(packet.placement.templates.dailyPlan.path,filename);
  assert.equal(packet.placement.templates.task.status,'bundled-reset');
});

test('latest policy queues visible upgrades and never bypasses a customized file', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  await save(f.input,old,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'latest'}]);
  let packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.automatic,true);
  assert.equal(packet.templates.dailyPlan.active.content,old.catalog.dailyPlan.content);
  assert.equal((await save(f.input,next)).status,'file-update-required');
  await writeFile(filename,next.catalog.dailyPlan.content);
  await save(f.input,next);
  await writeFile(filename,next.catalog.dailyPlan.content+'\nPersonal section\n');
  packet = await prepareTemplates(f.input,{catalog:catalog(3)});
  assert.equal(packet.templates.dailyPlan.automatic,false);
  assert.equal(packet.templates.dailyPlan.automaticBlocked,true);
  assert.equal(packet.templates.dailyPlan.shouldOffer,true);
  assert.match(packet.templates.dailyPlan.active.content,/Personal section/);
});

test('declining an automatically queued revision keeps latest policy without retrying that revision', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  await save(f.input,old,'decide',[{kind:'dailyPlan',action:'set-policy',policy:'latest'}]);
  await save(f.input,next);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  await save(f.input,next);
  const row = (await prepareTemplates(f.input,next)).templates.dailyPlan;
  assert.equal(row.fileUpdate,null);
  assert.equal(row.automatic,false);
  assert.equal(row.policy,'latest');
  assert.equal(await readFile(filename,'utf8'),old.catalog.dailyPlan.content);
  assert.equal((await prepareTemplates(f.input,{catalog:catalog(3)})).templates.dailyPlan.automatic,true);
});

test('the user can cancel a conflicted file upgrade without discarding local edits', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)};
  const filename = await materialize(f,old);
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'accept'}]);
  await writeFile(filename,'# Keep this new local edit\n');
  await save(f.input,next,'decide',[{kind:'dailyPlan',action:'decline'}]);
  const packet = await prepareTemplates(f.input,next);
  assert.equal(packet.templates.dailyPlan.fileUpdate,null);
  assert.equal(packet.templates.dailyPlan.shouldOffer,false);
  assert.equal(packet.templates.dailyPlan.active.content,'# Keep this new local edit\n');
});

test('resuming an approved file upgrade preserves its target across releases and logs only once', async () => {
  const f = await fixture(), old = {catalog:catalog(1)}, next = {catalog:catalog(2)}, later = {catalog:catalog(3)};
  const filename = await materialize(f,old);
  const prepared = await prepareTemplates(f.input,next);
  const request = {...f.input,action:'decide',expectedToken:prepared.token,
    decisions:[{kind:'dailyPlan',action:'accept'}],originalWords:'Use this new layout'};
  assert.equal((await saveTemplateState(request,next)).status,'file-update-required');
  assert.equal((await saveTemplateState(request,later)).status,'file-update-required');
  const resume = (await prepareTemplates(f.input,later)).templates.dailyPlan;
  assert.equal(resume.fileUpdate.target.content,next.catalog.dailyPlan.content);
  assert.equal(resume.shouldOffer,false);
  await writeFile(filename,resume.fileUpdate.target.content);
  await save(f.input,later);
  const finished = (await prepareTemplates(f.input,later)).templates.dailyPlan;
  assert.equal(finished.active.content,next.catalog.dailyPlan.content);
  assert.equal(finished.upstream.revision,next.catalog.dailyPlan.revision);
  assert.equal(finished.fileUpdate,null);
  assert.equal(finished.shouldOffer,true);
  const log = await queryDecisions({projectsRoot:path.join(f.input.vaultRoot,'1-projects'),dryRun:true});
  assert.equal(log.entries.length,1);
  assert.equal(log.entries[0].after.dailyPlan.pendingRevision,next.catalog.dailyPlan.revision);
});
