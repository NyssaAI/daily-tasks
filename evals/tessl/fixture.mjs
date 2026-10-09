import {mkdir,writeFile,readFile,rm} from 'node:fs/promises';
import path from 'node:path';
import crypto from 'node:crypto';
import {syncBuiltinESMExports} from 'node:module';
import {uuid7} from '../../lib/identity/identity.mjs';
import {localDay} from '../../lib/time/time.mjs';
import {planningBinding} from '../../lib/profile/context.mjs';
import {seedPlanningFixture} from '../planning-fixture.mjs';
const mode=process.argv[2];
const now='2026-10-09T15:00:00Z', timezone='America/Chicago';
// Fixture construction only: repeat identities without changing production code.
let entropyCounter=0;
crypto.randomBytes=size=>crypto.createHash('sha256').update('daily-tasks-fixture-v2:'+mode+':'+entropyCounter++).digest().subarray(0,size);
syncBuiltinESMExports();
Date.now=()=>Date.parse(now);
const today=localDay(now,timezone), previous='2026.10.08';
if(mode==='recovery') {
  const manifest=await seedPlanningFixture(path.resolve('vaults'),2,now);
  await rm(path.join(manifest.vaultRoot,'fixture.json'));
  await writeFile('ENVIRONMENT.md',JSON.stringify({vaultRoot:manifest.vaultRoot,now,timezone,runtimePackageRoot:path.resolve('support'),runtimeEntry:path.resolve('support/bin/daily-tasks.mjs'),user:{name:'Fixture',email:'fixture@example.test'},operationInterruptedAfter:'source selection removed; remaining effects unfinished'},null,2));
} else {
  const vaultRoot=path.resolve('vault'),projectsRoot=path.join(vaultRoot,'1-projects'), stateRoot=path.join(vaultRoot,'.nyssaai/daily-tasks'),dailyPlansRoot=path.join(vaultRoot,'2-areas/daily-plans');
  const project=path.join(projectsRoot,'website'), milestone=path.join(project,'m1-launch');
  for(const dir of [milestone,path.join(milestone,'inputs'),path.join(milestone,'outputs'),stateRoot,dailyPlansRoot])await mkdir(dir,{recursive:true});
  const ids=Object.fromEntries(['project','milestone','copy','review','criterion','milestoneCriterion','plan','priorPlan'].map(key=>[key,uuid7()]));
  const doc=(id,type,title,state,extra,body)=>'---\nid: '+id+'\ntype: '+type+'\ntitle: "'+title+'"\nowner: "casey@example.test"\n'+type+'-state: '+state+'\ncreated_at: "'+now+'"\nupdated_at: "'+now+'"\n'+extra+'---\n# '+title+'\n\n'+body+'\n';
  const copyLink='m1-launch/t1-draft-landing-copy',reviewLink='m1-launch/t2-review-launch-checklist';
  await writeFile(path.join(project,'project-index.md'),doc(ids.project,'project','Website','in-progress','', '## Project Summary\n\n| Milestone | Task | Description | Owner | Due Date |\n| --- | --- | --- | --- | --- |\n| [ ] [[m1-launch/m1-launch\\|Launch]] <!-- ref: '+ids.milestone+' --> | | Launch the website | Casey | — |\n| | [ ] [['+copyLink+'\\|Draft landing copy]] <!-- ref: '+ids.copy+' --> | Write copy | Casey | — |\n| | [ ] [['+reviewLink+'\\|Review launch checklist]] <!-- ref: '+ids.review+' --> | Review checklist | Casey | — |'));
  await writeFile(path.join(milestone,'m1-launch.md'),doc(ids.milestone,'milestone','Launch','in-progress','record_version: 2\nproject_id: '+ids.project+'\n','## Outcome\nPublic website is ready.\n\n## Definition of Done\n- [ ] Landing copy is approved and checklist reviewed. <!-- id: '+ids.milestoneCriterion+' -->\n\n## Tasks\n- [ ] [[t1-draft-landing-copy|Draft landing copy]] <!-- ref: '+ids.copy+' -->\n- [ ] [[t2-review-launch-checklist|Review launch checklist]] <!-- ref: '+ids.review+' -->'));
  await writeFile(path.join(milestone,'t1-draft-landing-copy.md'),doc(ids.copy,'task','Draft landing copy',mode==='closure'?'completed':'not-started','record_version: 2\nproject_id: '+ids.project+'\nmilestone_id: '+ids.milestone+'\n'+(mode==='closure'?'started_at: "2026-10-07T15:00:00Z"\nresolved_at: "2026-10-08T15:00:00Z"\n':''),'## Requirements\nWrite landing page copy.\n\n## Definition of Done\n- ['+(mode==='closure'?'x':' ')+'] Landing copy approved by Casey. <!-- id: '+uuid7()+' -->'));
  await writeFile(path.join(milestone,'t2-review-launch-checklist.md'),doc(ids.review,'task','Review launch checklist','in-progress','record_version: 2\nproject_id: '+ids.project+'\nmilestone_id: '+ids.milestone+'\nstarted_at: "2026-10-08T15:00:00Z"\n','## Requirements\nReview launch readiness.\n\n## Definition of Done\n- [x] Every launch checklist item reviewed. <!-- id: '+ids.criterion+' -->\n\n## Result\nCasey reviewed every item on 2026-10-08; all items are ready.'));
  if(mode!=='fresh')await writeFile(path.join(stateRoot,'profile.json'),JSON.stringify({schema_version:1,user:{name:'Casey',email:'casey@example.test'},timezone,priorities:[],vaultRoot:'.',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans',projectIndex:{ttlSeconds:14400}},null,2));
  const plan=(date,id,manual=false)=>'---\nid: '+id+'\ntype: daily-plan\ntitle: "Daily plan '+date+'"\ntimezone: "'+timezone+'"\ncreated_at: "'+now+'"\nupdated_at: "'+now+'"\n---\n# Daily plan '+date+'\n\n## My work\n- [ ] [[../../1-projects/website/'+copyLink+'|Draft landing copy]] <!-- ref: '+ids.copy+' -->\n'+(manual?'- [ ] Prepare launch announcement\n':'')+'\n## Notes\nPreserve this personal note.\n';
  if(['prior','edited','mapping','mixed','rollover'].includes(mode))await writeFile(path.join(dailyPlansRoot,previous+'-daily-plan.md'),plan(previous,ids.priorPlan));
  if(['mapping','mixed','edited','rollover'].includes(mode))await writeFile(path.join(dailyPlansRoot,today+'-daily-plan.md'),mode==='rollover'?plan(today,ids.plan).replace(copyLink,reviewLink).replace('Draft landing copy','Review launch checklist').replace(ids.copy,ids.review):plan(today,ids.plan,['mixed','edited'].includes(mode)));
  if(['mapping','mixed'].includes(mode)) {
    await mkdir(path.join(stateRoot,'review'),{recursive:true});
    await writeFile(path.join(stateRoot,'review',today+'.json'),JSON.stringify({schemaVersion:1,date:today,planId:ids.plan,mappingBinding:planningBinding({vaultRoot,projectsRoot,dailyPlansRoot}),mapping:{[ids.copy]:2,[ids.review]:4}},null,2));
  }
  await writeFile('ENVIRONMENT.md',JSON.stringify({vaultRoot,now,timezone,runtimePackageRoot:path.resolve('support'),runtimeEntry:path.resolve('support/bin/daily-tasks.mjs'),knownPeople:{Casey:'casey@example.test',Alex:'alex@example.test'},...(mode==='mapping'||mode==='mixed'?{activeScreen:{date:today,rows:{2:'Draft landing copy',4:'Review launch checklist'}}}:{})},null,2));
}
