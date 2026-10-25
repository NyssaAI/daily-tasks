import test from 'node:test';
import assert from 'node:assert/strict';
import { loadTemplateCatalog } from '#core/templates/catalog.mjs';
import { validateReviewScreen, validateDailyPlan } from '#core/planning/screen.mjs';
import { planningScreen, dailyPlanDocument } from './fixtures/planning-screen.mjs';
import { mkdir, mkdtemp, writeFile, readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { preparePlanning, savePlanningState } from '#core/planning/session.mjs';
import { completeChangedRollover, completeOperation } from '#core/operations/verification.mjs';
import { parseChecklist } from '#core/planning/planning.mjs';

const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12,'0')}`;
const review = {counts:{openProjects:1,openTasks:1,lateTasks:0},selected:[
  {id:id(1),number:7,state:'in-progress',title:'Ongoing',owner:'owner@example.test',carriedFrom:'2026.10.12'}
],available:[{id:id(2),number:12,state:'not-started',title:'Available',owner:'owner@example.test'}]};

test('review validation accepts the active screen and rejects prose, wrong layout and invented rows', async () => {
  const active = (await loadTemplateCatalog()).planDayReview;
  const draft = planningScreen({review});
  assert.equal(validateReviewScreen(draft,active,review).valid,true);
  const variants = [
    ['prose','You have two tasks. Which would you like?'],
    ['missing section',draft.replace('## Available tasks','## Suggestions')],
    ['missing column',draft.replaceAll(' | Owner','')],
    ['missing row',draft.split('\n').filter(line => !line.includes(id(2))).join('\n')],
    ['wrong row number',draft.replace('| 12 |','| 13 |')],
    ['number in wrong column',draft.replace('| 7 |','| 99 |').replace('| Project |','| 7 |')],
    ['wrong status',draft.replace('| 7 | [>]','| 7 | [x]')],
    ['wrong count',draft.replace('Open tasks: 1','Open tasks: 9')],
    ['missing provenance',draft.replace('↺ [Ongoing]','[Ongoing]')],
    ['code fence',`\`\`\`markdown\n${draft}\`\`\``],
    ['wrong identity',draft.replace(id(2),id(3))]
  ];
  for (const [name,markdown] of variants) assert.equal(validateReviewScreen(markdown,active,review).valid,false,name);
  const selectedRow = draft.split('\n').find(line => line.includes(id(1)));
  const availableRow = draft.split('\n').find(line => line.includes(id(2)));
  const swapped = draft.replace(selectedRow,'REPLACEMENT_ROW').replace(availableRow,selectedRow).replace('REPLACEMENT_ROW',availableRow);
  assert.equal(validateReviewScreen(swapped,active,review).valid,false,'Rows cannot swap selected and available sections');
});

test('review validation follows custom table headings and column order rather than the bundled layout', async () => {
  const bundled = (await loadTemplateCatalog()).planDayReview;
  const replace = text => text.replaceAll('Already selected','Continuing').replaceAll('Available tasks','Choose next')
    .replaceAll('Update your plan','Your decision').replaceAll('| # | Status |','| Status | # |');
  const active = {...bundled,content:replace(bundled.content.replace('| #  | Status |','| # | Status |'))};
  const draft = replace(planningScreen({review})).replace('| 7 | [>] |','| [>] | 7 |').replace('| 12 | [ ] |','| [ ] | 12 |');
  assert.equal(validateReviewScreen(draft,active,review).valid,true);
  assert.equal(validateReviewScreen(planningScreen({review}),active,review).valid,false);
});

test('review validation permits custom numbered checklists and empty-state prose without sample rows', async () => {
  const active = {content:'# Review\n## Current\n- 1. [ ] Sample <!-- ref: SAMPLE -->\n## Choices\n- 2. [ ] Sample <!-- ref: SAMPLE -->\n'};
  const draft = `# Review\n## Current\n- 7. [>] ↺ [Ongoing](task.md) <!-- ref: ${id(1)} -->\n## Choices\n- 12. [ ] [Available](task.md) <!-- ref: ${id(2)} -->\nLegend: [ ] not started · [>] in progress · [x] completed · [-] cancelled\n`;
  assert.equal(validateReviewScreen(draft,active,review).valid,true);
  assert.equal(validateReviewScreen('# Review\n## Current\nNone.\n## Choices\nNone.\nLegend: [ ] · [>] · [x] · [-]',active,
    {counts:{openProjects:0,openTasks:0,lateTasks:0},selected:[],available:[]}).valid,true);
});

test('daily plan validation accepts the active dailyPlan template and rejects bullet checklists, missing sections, or wrong columns', async () => {
  const active = (await loadTemplateCatalog()).dailyPlan;
  const draft = dailyPlanDocument({id:id(20),counts:review.counts,selected:review.selected,userEmail:'owner@example.test'});
  const valid = validateDailyPlan(draft,active,{selected:review.selected,counts:review.counts,userEmail:'owner@example.test'});
  assert.equal(valid.valid,true,JSON.stringify(valid.errors));
  const bulletChecklist = draft.replace(/#### Project \/ Milestone[\s\S]*?(?=\n### Delegated work)/,`- [>] ↺ [[../projects/task|Ongoing]] <!-- ref: ${id(1)} -->\n`);
  const rejectedChecklist = validateDailyPlan(bulletChecklist,active,{selected:review.selected,counts:review.counts,userEmail:'owner@example.test'});
  assert.equal(rejectedChecklist.valid,false);
  assert.ok(rejectedChecklist.errors.some(err => /table/i.test(err)));
  const missingHeading = draft.replace('### Delegated work','### Other work');
  assert.equal(validateDailyPlan(missingHeading,active,{selected:review.selected,counts:review.counts,userEmail:'owner@example.test'}).valid,false);
  const wrongResponsibility = draft
    .replace('### My work\n\n#### Project / Milestone','### My work\n\nNo work.\n\n### Delegated work\n\n#### Project / Milestone')
    .replace('\n### Delegated work\n\nNo work selected for this section.','');
  assert.equal(validateDailyPlan(wrongResponsibility,active,{selected:review.selected,counts:review.counts,userEmail:'owner@example.test'}).valid,false);
});

test('save-review requires a validated draft, persists it and rejects a changed template with the same row mapping', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/review-screen-')));
  const vaultRoot = path.join(root,'workspace'), homeRoot = path.join(root,'home');
  const config = path.join(vaultRoot,'.nyssa-ai/daily-tasks');
  for (const directory of [config,homeRoot,path.join(vaultRoot,'projects'),path.join(vaultRoot,'daily')]) await mkdir(directory,{recursive:true});
  const templatePath = path.join(vaultRoot,'review.md');
  const active = (await loadTemplateCatalog()).planDayReview;
  await writeFile(templatePath,active.content);
  await writeFile(path.join(config,'profile.json'),JSON.stringify({schema_version:2,user:{name:'Owner',email:'owner@example.test'},
    timezone:'UTC',projectsRoot:'./projects',dailyPlansRelative:'daily',templates:{planDayReview:'./review.md'}}));
  const planPath = path.join(vaultRoot,'daily/2026.10.13-daily-plan.md');
  await writeFile(planPath,`---\nid: ${id(20)}\ntype: daily-plan\ntitle: "Daily plan 2026.10.13"\ntimezone: "UTC"\n---\n# Daily plan — 2026.10.13\n\nPlain prose plan ignoring the dailyPlan template.\n`);
  const input = {vaultRoot,homeRoot,now:'2026-10-13T14:00:00Z'};
  const badPlanPacket = await preparePlanning(input);
  assert.equal(badPlanPacket.current.templateValidation.valid,false);
  await assert.rejects(savePlanningState({
    ...input,action:'save-review',expectedPlanHash:badPlanPacket.current.sha256,expectedPreviousHash:null,
    expectedStateHash:null,expectedInventoryHash:badPlanPacket.inventoryHash,expectedReviewHash:badPlanPacket.reviewHash,
    reviewMarkdown:planningScreen(badPlanPacket),
  }),/Daily plan does not match the active dailyPlan template/);
  await writeFile(planPath,dailyPlanDocument({id:id(20),counts:{openProjects:0,openTasks:0,lateTasks:0},selected:[]}));
  const packet = await preparePlanning(input);
  assert.equal(packet.current.templateValidation.valid,true);
  const request = {...input,action:'save-review',expectedPlanHash:packet.current.sha256,expectedPreviousHash:null,
    expectedStateHash:null,expectedInventoryHash:packet.inventoryHash,expectedReviewHash:packet.reviewHash};
  await assert.rejects(savePlanningState(request),/reviewMarkdown/);
  await assert.rejects(savePlanningState({...request,reviewMarkdown:'Nothing to do. What next?'}),/screen|template/i);
  const markdown = planningScreen(packet);
  const preview = await savePlanningState({...request,reviewMarkdown:markdown,dryRun:true});
  assert.equal(preview.status,'preview');
  await assert.rejects(readFile(packet.state.review.path),{code:'ENOENT'});
  const saved = await savePlanningState({...request,reviewMarkdown:markdown});
  assert.equal(saved.value.screen.markdown,markdown);
  assert.equal(saved.value.screen.templateRevision,active.revision);
  assert.equal(JSON.parse(await readFile(saved.path,'utf8')).screen.markdown,markdown);
  const beforeChange = await preparePlanning(input);
  await writeFile(templatePath,active.content.replace('## Available tasks','## Choose your work'));
  const changed = await preparePlanning(input);
  assert.deepEqual(changed.review.mapping,beforeChange.review.mapping);
  assert.notEqual(changed.reviewHash,beforeChange.reviewHash);
  await assert.rejects(savePlanningState({...request,expectedStateHash:beforeChange.state.review.sha256,
    expectedReviewHash:beforeChange.reviewHash,reviewMarkdown:markdown}),/review changed/i);
  await assert.rejects(savePlanningState({...request,expectedStateHash:changed.state.review.sha256,
    expectedReviewHash:changed.reviewHash,reviewMarkdown:markdown}),/heading|template/i);
});


test('review screen requires the correct project page indicator', async () => {
  const active = (await loadTemplateCatalog()).planDayReview;
  const paged = {...review,page:1,pageCount:4};
  const draft = planningScreen({review:paged});
  assert.equal(validateReviewScreen(draft,active,paged).valid,true);
  assert.equal(validateReviewScreen(draft.replace('Page 2 of 4','Page 1 of 4'),active,paged).valid,false);
  assert.equal(validateReviewScreen(draft.replace('Page 2 of 4',''),active,paged).valid,false);
});

test('table parsers and validators accept unescaped wiki-link pipes inside Markdown table cells', async () => {
  const catalog = await loadTemplateCatalog();
  const unescapedTemplate = {
    ...catalog.dailyPlan,
    content: catalog.dailyPlan.content.replaceAll('\\|', '|'),
  };
  const draft = dailyPlanDocument({id:id(20),counts:review.counts,selected:review.selected,userEmail:'owner@example.test'})
    .replaceAll('\\|', '|');
  const validated = validateDailyPlan(draft, unescapedTemplate, {selected:review.selected,counts:review.counts,userEmail:'owner@example.test'});
  assert.equal(validated.valid, true, JSON.stringify(validated.errors));
  const parsed = parseChecklist(draft);
  assert.equal(parsed.length, 1);
  assert.equal(parsed[0].id, id(1));
  assert.equal(parsed[0].label, 'Ongoing');
});

test('planning-prepare drafts complete create-plan rollover, save-review and selection in 2 steps without manual table construction', async () => {
  await mkdir('.temp',{recursive:true});
  const root = await realpath(await mkdtemp(path.resolve('.temp/drafts-flow-')));
  const vaultRoot = path.join(root,'workspace'), homeRoot = path.join(root,'home');
  const config = path.join(vaultRoot,'.nyssa-ai/daily-tasks');
  const projectDir = path.join(vaultRoot,'projects/alpha/m1-first');
  const dailyDir = path.join(vaultRoot,'daily');
  for (const directory of [config,homeRoot,projectDir,dailyDir]) await mkdir(directory,{recursive:true});
  await writeFile(path.join(config,'profile.json'),JSON.stringify({
    schema_version:2,
    user:{name:'Owner',email:'owner@example.test'},
    timezone:'UTC',
    projectsRoot:'./projects',
    dailyPlansRelative:'daily',
  }));
  const projectId = id(10), milestoneId = id(11), carriedTaskId = id(12), availableTaskId = id(13), prevPlanId = id(14);
  const now = '2026-10-13T14:00:00.000Z';
  await writeFile(path.join(vaultRoot,'projects/alpha/project-index.md'),
    `---\nid: ${projectId}\ntype: project\ntitle: "Alpha Project"\nowner: owner@example.test\nproject-state: in-progress\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# Alpha Project\n- [>] [[m1-first/m1-first|First Milestone]] <!-- ref: ${milestoneId} -->\n`);
  await writeFile(path.join(projectDir,'m1-first.md'),
    `---\nid: ${milestoneId}\ntype: milestone\ntitle: "First Milestone"\nowner: owner@example.test\nmilestone-state: in-progress\nproject_id: ${projectId}\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# First Milestone\n- [ ] [[t1-carried|Carried Task]] <!-- ref: ${carriedTaskId} -->\n- [ ] [[t2-available|Available Task]] <!-- ref: ${availableTaskId} -->\n`);
  await writeFile(path.join(projectDir,'t1-carried.md'),
    `---\nid: ${carriedTaskId}\ntype: task\ntitle: "Carried Task"\nowner: owner@example.test\ntask-state: not-started\nproject_id: ${projectId}\nmilestone_id: ${milestoneId}\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# Carried Task\n`);
  await writeFile(path.join(projectDir,'t2-available.md'),
    `---\nid: ${availableTaskId}\ntype: task\ntitle: "Available Task"\nowner: owner@example.test\ntask-state: not-started\nproject_id: ${projectId}\nmilestone_id: ${milestoneId}\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# Available Task\n`);
  // Previous plan with unescaped wiki-link pipe in table
  await writeFile(path.join(dailyDir,'2026.10.12-daily-plan.md'),
    `---\nid: ${prevPlanId}\ntype: daily-plan\ntitle: "Daily plan 2026.10.12"\ntimezone: "UTC"\ncreated_at: "${now}"\nupdated_at: "${now}"\n---\n# Daily plan — 2026.10.12\n\n| # | Status | Project | Milestone | Task | Due Date |\n| --- | --- | --- | --- | --- | --- |\n| 1 | [ ] | Alpha Project | First Milestone | [[../projects/alpha/m1-first/t1-carried|Carried Task]] <!-- ref: ${carriedTaskId} --> | — |\n`);

  const prep = await preparePlanning({vaultRoot,homeRoot,now});
  assert.equal(prep.status,'create-plan');
  assert.equal(prep.rollover.unresolved.length,0);
  assert.ok(prep.drafts?.rolloverOperation);
  await mkdir(path.dirname(prep.drafts.rolloverOperation.operationPath),{recursive:true});
  await writeFile(prep.drafts.rolloverOperation.operationPath,JSON.stringify(prep.drafts.rolloverOperation.checkpoint,null,2));
  await writeFile(prep.current.path,prep.drafts.dailyPlanMarkdown);
  const completed = await completeChangedRollover(prep.drafts.rolloverOperation.completeInput);
  assert.equal(completed.status,'completed');
  assert.equal(completed.reviewSaved?.status,'saved');
  assert.match(completed.reviewSaved.value.screen.markdown,/Carried Task/);
  assert.match(completed.reviewSaved.value.screen.markdown,/Available Task/);
  assert.doesNotMatch(completed.reviewSaved.value.screen.markdown,/\[\[/,'Review screen should not show wiki-link task paths');
  assert.match(prep.drafts.dailyPlanMarkdown,/\[\[/,'Saved daily plan keeps Obsidian wiki-links');

  // Now select availableTaskId using selectionOperation draft
  const selPrep = await preparePlanning({
    vaultRoot,homeRoot,now,
    selection:{action:'add',taskIds:[availableTaskId],originalWords:'Add 2 to today'},
  });
  assert.ok(selPrep.drafts?.selectionOperation);
  await writeFile(selPrep.drafts.selectionOperation.operationPath,JSON.stringify(selPrep.drafts.selectionOperation.checkpoint,null,2));
  await writeFile(selPrep.drafts.selectionOperation.planPath,selPrep.drafts.selectionOperation.dailyPlanMarkdown);
  const selDone = await completeOperation(selPrep.drafts.selectionOperation.completeInput);
  assert.equal(selDone.status,'completed');
  assert.equal(selDone.reviewSaved?.status,'saved');
  assert.equal(selDone.prepared.review.selected.length,2);
});
