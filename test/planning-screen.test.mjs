import test from 'node:test';
import assert from 'node:assert/strict';
import { loadTemplateCatalog } from '#core/templates/catalog.mjs';
import { validateReviewScreen } from '#core/planning/screen.mjs';
import { planningScreen } from './fixtures/planning-screen.mjs';
import { mkdir, mkdtemp, writeFile, readFile, realpath } from 'node:fs/promises';
import path from 'node:path';
import { preparePlanning, savePlanningState } from '#core/planning/session.mjs';

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
  await writeFile(path.join(vaultRoot,'daily/2026.10.13-daily-plan.md'),`---\nid: ${id(20)}\ntype: daily-plan\n---\n`);
  const input = {vaultRoot,homeRoot,now:'2026-10-13T14:00:00Z'};
  const packet = await preparePlanning(input);
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
