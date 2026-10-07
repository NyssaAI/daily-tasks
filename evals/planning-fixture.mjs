import { mkdir, mkdtemp, readFile, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { fileURLToPath } from 'node:url';
import { isDeepStrictEqual } from 'node:util';
import { uuid7 } from '../lib/identity/identity.mjs';
import { localDay, utcTimestamp } from '../lib/time/time.mjs';
import { planningBinding } from '../lib/profile/context.mjs';
import { parseChecklist } from '../lib/planning/planning.mjs';
import { recoverOperation } from '../lib/reconciliation/reconciliation.mjs';
import { appendDecision, queryDecisions } from '../lib/log/decision-log.mjs';
import { projectInventory } from '../lib/inventory/inventory.mjs';

export const planningHash = text => createHash('sha256').update(text).digest('hex');
const json = value => JSON.stringify(value,null,2)+'\n';

/** Synthetic fault fixture only. Creates starting artifacts, never resumes user work. */
export async function seedPlanningFixture(parent, stopAfter = 0, now = new Date().toISOString()) {
  if (!Number.isInteger(stopAfter) || stopAfter < 0 || stopAfter > 4) throw new TypeError('stopAfter must be 0..4');
  await mkdir(parent,{recursive:true});
  const vaultRoot = await mkdtemp(path.join(path.resolve(parent),'planning-'));
  const projectsRoot = path.join(vaultRoot,'1-projects');
  const dailyPlansRoot = path.join(vaultRoot,'2-areas/daily-plans');
  const stateRoot = path.join(vaultRoot,'.nyssaai/daily-tasks');
  const project = path.join(projectsRoot,'2026.01.01-fixture');
  for (const dir of [path.join(project,'first'),dailyPlansRoot,path.join(stateRoot,'operations')]) await mkdir(dir,{recursive:true});
  const ids = Object.fromEntries(['project','milestone','task','other','source','destination','operation','event','rollover','history'].map(key => [key,uuid7()]));
  const userEmail = 'fixture@example.test', timezone = 'America/Chicago';
  const today = localDay(now,timezone);
  const nextDay = localDay(new Date(Date.parse(today.replaceAll('.','-')+'T12:00:00Z')+86400000).toISOString(),timezone);
  const doc = (id,type,title,extra='',body='') => `---\nid: ${id}\ntype: ${type}\ntitle: "${title}"\nowner: ${userEmail}\n${type}-state: not-started\ncreated_at: ${now}\nupdated_at: ${now}\n${extra}---\n# ${title}\n${body}\n`;
  await writeFile(path.join(project,'project-index.md'),doc(ids.project,'project','Fixture','',`| Milestone | Task |\n| --- | --- |\n| [ ] [[first/milestone\\|First]] <!-- ref: ${ids.milestone} --> | |\n| | [ ] [[first/recovery-task\\|Recovery task]] <!-- ref: ${ids.task} --> |\n| | [ ] [[first/other-task\\|Other task]] <!-- ref: ${ids.other} --> |`));
  await writeFile(path.join(project,'first/milestone.md'),doc(ids.milestone,'milestone','First',`project_id: ${ids.project}\n`));
  for (const [key,title] of [['task','Recovery task'],['other','Other task']]) await writeFile(path.join(project,`first/${key === 'task' ? 'recovery' : 'other'}-task.md`),doc(ids[key],'task',title,`project_id: ${ids.project}\nmilestone_id: ${ids.milestone}\n`));
  const canonicalHashes = Object.fromEntries(await Promise.all(['project-index.md','first/milestone.md','first/recovery-task.md','first/other-task.md'].map(async filename => {
    const absolute = path.join(project,filename);
    return [absolute,planningHash(await readFile(absolute,'utf8'))];
  })));
  const link = key => `../../1-projects/2026.01.01-fixture/first/${key === 'task' ? 'recovery' : 'other'}-task`;
  const taskRow = `- [ ] [[${link('task')}|Recovery task]] <!-- ref: ${ids.task} -->\n`;
  const otherRow = `- [ ] [[${link('other')}|Other task]] <!-- ref: ${ids.other} -->\n`;
  const plan = (date,id,rows) => `---\nid: ${id}\ntype: daily-plan\ntitle: "Daily plan ${date}"\ndocument-maturity: reviewed\ntimezone: "${timezone}"\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# Daily plan — ${date}\n\n**Timezone:** ${timezone}\n\n## My work\n\n${rows}\n## Notes\n\nPreserve this unrelated note.\n`;
  const source = path.join(dailyPlansRoot,`${today}-daily-plan.md`), destination = path.join(dailyPlansRoot,`${nextDay}-daily-plan.md`);
  const sourceBefore = plan(today,ids.source,taskRow+otherRow), sourceAfter = plan(today,ids.source,otherRow);
  const destinationAfter = plan(nextDay,ids.destination,taskRow);
  const previousDay = localDay(new Date(Date.parse(today.replaceAll('.','-')+'T12:00:00Z')-86400000).toISOString(),timezone);
  const historyPath = path.join(dailyPlansRoot,previousDay+'-daily-plan.md');
  const historyText = plan(previousDay,ids.history,taskRow);
  await writeFile(historyPath,historyText);
  const baselinePath = path.join(stateRoot,'reconciliation.json');
  const baseline = (moved) => ({schemaVersion:1,records:{[ids.task]:{canonical:{state:'not-started'},views:{
    [source]:{selected:!moved,hash:planningHash(moved ? sourceAfter : sourceBefore)},
    ...(moved ? {[destination]:{selected:true,hash:planningHash(destinationAfter)}} : {})
  }}}});
  const baselineBefore = json(baseline(false)), baselineAfter = json(baseline(true));
  await mkdir(path.join(stateRoot,'rollover'),{recursive:true});
  const sourceRolloverPath = path.join(stateRoot,'rollover',today+'.json');
  const destinationRolloverPath = path.join(stateRoot,'rollover',nextDay+'.json');
  const sourceRolloverBefore = {schemaVersion:1,date:today,planId:ids.source,operationId:ids.rollover,completedAt:now,removedIds:[]};
  const sourceRolloverAfter = {...sourceRolloverBefore,removedIds:[ids.task]};
  const destinationRollover = {schemaVersion:1,date:nextDay,planId:ids.destination,removedIds:[]};
  await writeFile(sourceRolloverPath,json(sourceRolloverBefore));
  await writeFile(destinationRolloverPath,json(destinationRollover));
  const event = {id:ids.event,operation_id:ids.operation,action:'selection-move',record_ids:[ids.task],actor:{kind:'person',id:userEmail},activity_at:now,recorded_at:now,time_defaulted:false,
    original_words:'Move Recovery task to tomorrow (synthetic acceptance test).',before:{date:today},after:{date:nextDay}};
  const changes = [
    {key:'destinationMember',before:{present:true,value:false},after:{present:true,value:true}},
    {key:'sourceMember',before:{present:true,value:true},after:{present:true,value:false}},
    {key:'logRecorded',before:{present:true,value:false},after:{present:true,value:true}},
    {key:'baselineHash',before:{present:true,value:planningHash(baselineBefore)},after:{present:true,value:planningHash(baselineAfter)}},
    {key:'sourceRolloverHash',before:{present:true,value:planningHash(json(sourceRolloverBefore))},after:{present:true,value:planningHash(json(sourceRolloverAfter))}}
  ];
  const operation = {operation_id:ids.operation,contextBinding:planningBinding({vaultRoot,projectsRoot,dailyPlansRoot}),changes,event,
    files:[{path:source,before:planningHash(sourceBefore),after:planningHash(sourceAfter)},
      {path:destination,before:null,after:planningHash(destinationAfter)}]};
  const checkpointPath = path.join(stateRoot,'operations',ids.operation+'.json');
  await writeFile(source,stopAfter >= 2 ? sourceAfter : sourceBefore);
  if (stopAfter >= 1) await writeFile(destination,destinationAfter);
  await writeFile(baselinePath,stopAfter >= 4 ? baselineAfter : baselineBefore);
  await writeFile(path.join(stateRoot,'profile.json'),json({schema_version:1,user:{name:'Fixture',email:userEmail},timezone,priorities:[],vaultRoot:'.',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans',projectIndex:{ttlSeconds:14400}}));
  await writeFile(checkpointPath,json(operation));
  if (stopAfter >= 3) await appendDecision({projectsRoot,entry:event});
  const manifest = {vaultRoot,projectsRoot,dailyPlansRoot,stateRoot,timezone,now,userEmail,today,nextDay,ids,canonicalHashes,source,destination,sourceBefore,sourceAfter,destinationAfter,historyPath,historyHash:planningHash(historyText),baselinePath,baselineBefore,baselineAfter,sourceRolloverPath,destinationRolloverPath,sourceRolloverBefore,sourceRolloverAfter,destinationRollover,checkpointPath,operation,stopAfter};
  await writeFile(path.join(vaultRoot,'fixture.json'),json(manifest));
  return manifest;
}

/** Read-only workflow oracle apart from disposable inventory refresh and log-query locks. */
export async function inspectPlanningFixture(fixture) {
  const {source,destination,ids,operation,baselinePath,projectsRoot} = fixture;
  const sourceText = await readFile(source,'utf8');
  let destinationText;
  try { destinationText = await readFile(destination,'utf8'); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const baselineText = await readFile(baselinePath,'utf8');
  const sourceRolloverText = await readFile(fixture.sourceRolloverPath,'utf8');
  const destinationRollover = JSON.parse(await readFile(fixture.destinationRolloverPath,'utf8'));
  const historyPreserved = fixture.historyPath ? planningHash(await readFile(fixture.historyPath,'utf8')) === fixture.historyHash : false;
  // Query the whole bounded fixture history: a changed record_ids must not hide
  // an operation/event collision from the exact-payload comparison.
  const log = await queryDecisions({projectsRoot,limit:1000});
  const recorded = log.entries.find(entry => entry.operation_id === ids.operation);
  const actual = {sourceMember:parseChecklist(sourceText).some(row => row.id === ids.task),destinationMember:parseChecklist(destinationText ?? '').some(row => row.id === ids.task),logRecorded:recorded ? isDeepStrictEqual(recorded,operation.event) ? true : 'conflicting-event' : false,baselineHash:planningHash(baselineText),sourceRolloverHash:planningHash(sourceRolloverText)};
  const recovery = recoverOperation(operation,actual);
  const unexpectedFiles = operation.files.filter(file => {
    const text = file.path === source ? sourceText : destinationText;
    const hash = text === undefined ? null : planningHash(text);
    return hash !== file.before && hash !== file.after;
  }).map(file => file.path);
  const changedCanonical = [];
  for (const [filename,expected] of Object.entries(fixture.canonicalHashes ?? {})) {
    if (planningHash(await readFile(filename,'utf8')) !== expected) changedCanonical.push(filename);
  }
  const canonicalPreserved = Object.keys(fixture.canonicalHashes ?? {}).length === 4 && !changedCanonical.length;
  unexpectedFiles.push(...changedCanonical);
  const {inventory} = await projectInventory({...fixture,forceRefresh:true});
  const active = inventory.tasks.find(task => task.id === ids.task)?.planned ?? [];
  let checkpoint;
  try { checkpoint = JSON.parse(await readFile(fixture.checkpointPath,'utf8')); } catch (error) { if (error.code !== 'ENOENT') throw error; }
  const completion = checkpoint?.completedAt;
  // The operation protocol permits removing a completed checkpoint. The immutable
  // fixture intent still supplies the comparison, but absence is safe only when
  // every persisted effect is already applied; it cannot excuse pending work.
  const checkpointRemoved = !checkpoint && recovery.status === 'already-applied';
  const checkpointIntentPreserved = checkpointRemoved || !!checkpoint && isDeepStrictEqual(Object.fromEntries(Object.keys(operation).map(key => [key,checkpoint[key]])),operation);
  if (!checkpointIntentPreserved) unexpectedFiles.push(fixture.checkpointPath);
  let completionValid = completion === undefined;
  if (completion !== undefined) { try { utcTimestamp(completion); completionValid = true; } catch { /* Invalid completion is not evidence. */ } }
  return {recovery,unexpectedFiles,actual,logCount:log.entries.length,active,
    otherPreserved:parseChecklist(sourceText).some(row => row.id === ids.other),
    prosePreserved:sourceText.includes('Preserve this unrelated note.') && (!destinationText || destinationText.includes('Preserve this unrelated note.')),
    planIdentityPreserved:!destinationText || destinationText.includes(`id: ${ids.destination}`),completion,
    canonicalPreserved,checkpointIntentPreserved,checkpointRemoved,completionValid,historyPreserved,rolloverPreserved:JSON.parse(sourceRolloverText).operationId === fixture.ids.rollover && isDeepStrictEqual(destinationRollover,fixture.destinationRollover),
    verified:recovery.status === 'already-applied' && !unexpectedFiles.length && canonicalPreserved && checkpointIntentPreserved && completionValid && log.entries.length === 1 && active.length === 1 && active[0].date === fixture.nextDay && historyPreserved && isDeepStrictEqual(destinationRollover,fixture.destinationRollover)};
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const mode = process.argv[2];
  if (mode === 'seed') {
    const fixture = await seedPlanningFixture(process.argv[3],Number(process.argv[4] ?? 0));
    console.log(JSON.stringify({fixture:path.join(fixture.vaultRoot,'fixture.json'),vaultRoot:fixture.vaultRoot,stopAfter:fixture.stopAfter}));
  } else if (mode === 'inspect') console.log(JSON.stringify(await inspectPlanningFixture(JSON.parse(await readFile(process.argv[3],'utf8'))),null,2));
  else throw new Error('Use planning-fixture.mjs seed ABSOLUTE_SCRATCH_DIR [0..4] or inspect ABSOLUTE_FIXTURE_JSON');
}
