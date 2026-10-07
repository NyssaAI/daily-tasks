import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdir, mkdtemp, readFile, writeFile, realpath, unlink, cp } from 'node:fs/promises';
import path from 'node:path';
import { projectInventory, invalidateInventory } from '../lib/inventory/inventory.mjs';
import { planningReview, planSelection, maintenanceStatus } from '../lib/planning/review.mjs';
import { carryForward } from '../lib/planning/planning.mjs';
import { resolveContext, planningBinding } from '../lib/profile/context.mjs';
import { preparePlanning, savePlanningState } from '../lib/planning/session.mjs';

const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12,'0')}`;
const now = '2026-10-06T14:00:00.000Z';
const owner = 'owner@example.test';
const doc = (n,type,title,extra='',body='') => `---\nid: ${id(n)}\ntype: ${type}\ntitle: "${title}"\nowner: ${owner}\n${type}-state: not-started\ncreated_at: ${now}\nupdated_at: ${now}\n${extra}---\n# ${title}\n${body}\n`;
async function fixture() {
  await mkdir('.temp',{recursive:true});
  const vaultRoot = await realpath(await mkdtemp(path.resolve('.temp/inventory-')));
  const projectsRoot = path.join(vaultRoot,'1-projects'), dailyPlansRoot = path.join(vaultRoot,'2-areas/daily-plans');
  const project = path.join(projectsRoot,'2026.01.01-alpha');
  await mkdir(path.join(project,'first'),{recursive:true});
  await mkdir(path.join(project,'second'),{recursive:true});
  await mkdir(dailyPlansRoot,{recursive:true});
  await writeFile(path.join(project,'project-index.md'),doc(1,'project','Alpha','',`| Milestone | Task |\n| --- | --- |\n| [ ] [[first/milestone\\|First]] <!-- ref: ${id(2)} --> | |\n| | [ ] [[first/a\\|A]] <!-- ref: ${id(3)} --> |\n| | [ ] [[first/b\\|B]] <!-- ref: ${id(4)} --> |\n| [ ] [[second/milestone\\|Second]] <!-- ref: ${id(5)} --> | |\n| | [ ] [[second/c\\|C]] <!-- ref: ${id(6)} --> |`));
  await writeFile(path.join(project,'first/milestone.md'),doc(2,'milestone','First',`project_id: ${id(1)}\n`));
  await writeFile(path.join(project,'second/milestone.md'),doc(5,'milestone','Second',`project_id: ${id(1)}\n`));
  for (const [n,file,m] of [[3,'first/a.md',2],[4,'first/b.md',2],[6,'second/c.md',5]]) await writeFile(path.join(project,file),doc(n,'task',file,`project_id: ${id(1)}\nmilestone_id: ${id(m)}\ntarget_date: 2026-10-05T05:00:00Z\n`));
  const future = path.join(dailyPlansRoot,'2026.10.07-daily-plan.md');
  await writeFile(future,`---\nid: ${id(20)}\ntype: daily-plan\n---\n## My work\n- [ ] [[../../1-projects/2026.01.01-alpha/first/b|B]] <!-- ref: ${id(4)} -->\n`);
  return {vaultRoot,projectsRoot,dailyPlansRoot,project,future,timezone:'America/Chicago',now};
}

test('context navigation and unidentified legacy projects cannot erase unrelated managed work', async () => {
  const input = await fixture();
  const index = path.join(input.project,'project-index.md');
  await writeFile(index,(await readFile(index,'utf8')) + '\n## References\nRead [[research]] and [[brief.pdf]].\n');
  for (const name of ['legacy-a','legacy-b']) {
    await mkdir(path.join(input.projectsRoot,name));
    await writeFile(path.join(input.projectsRoot,name,'project-index.md'),'# Legacy project\n[[notes]]\n');
  }
  const {inventory} = await projectInventory(input);
  assert.deepEqual(inventory.tasks.map(t => t.id),[id(3),id(4),id(6)]);
  assert.ok(!inventory.diagnostics.some(d => d.code === 'invalid-planning-scope' && d.projectId === id(1)));
  assert.deepEqual(planningReview({inventory,userEmail:owner,timezone:input.timezone,now}).available.map(t => t.id),[id(3)]);
});

test('maintained preparation binds actual plan identity and state writes reject stale or task-shaped inputs', async () => {
  const input = await fixture();
  await mkdir(path.join(input.vaultRoot,'.nyssaai/daily-tasks'),{recursive:true});
  await writeFile(path.join(input.vaultRoot,'.nyssaai/daily-tasks/profile.json'),'\uFEFF'+JSON.stringify({schema_version:1,
    user:{name:'Owner',email:owner},timezone:input.timezone,priorities:[],vaultRoot:'./',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans'}));
  const plan = path.join(input.dailyPlansRoot,'2026.10.06-daily-plan.md');
  await writeFile(plan,`---\nid: ${id(21)}\ntype: daily-plan\n---\n- [ ] [[../../1-projects/2026.01.01-alpha/first/a|A]] <!-- ref: ${id(3)} -->\n`);
  const prepared = await preparePlanning(input);
  assert.equal(prepared.status,'prepared');
  await writeFile(path.join(input.vaultRoot,'.nyssaai/daily-tasks/planning-review.json'),JSON.stringify({date:prepared.context.localDate,
    mappingBinding:prepared.context.planningBinding,mapping:{[id(3)]:7}}));
  const legacy = await preparePlanning(input);
  assert.equal(legacy.review.selected[0].number,7);
  const savedReview = await savePlanningState({...input,action:'save-review',expectedPlanHash:legacy.current.sha256,
    expectedPreviousHash:null,expectedStateHash:legacy.state.review.sha256,expectedInventoryHash:legacy.inventoryHash,expectedReviewHash:legacy.reviewHash});
  const reopenedReview = JSON.parse(await readFile(savedReview.path,'utf8'));
  assert.equal(reopenedReview.planId,id(21));
  assert.equal(reopenedReview.mapping[id(3)],7);
  assert.equal((await preparePlanning(input)).review.selected[0].number,7);
  assert.equal(prepared.current.id,id(21));
  assert.equal(prepared.rollover.unresolved.length,0);
  assert.equal(prepared.review.selected[0].id,id(3));
  const stateInput = {...input,action:'complete-rollover',expectedPlanHash:prepared.current.sha256,expectedPreviousHash:null,expectedStateHash:null,expectedInventoryHash:prepared.inventoryHash};
  const saved = await savePlanningState(stateInput);
  assert.equal(saved.value.planId,id(21));
  assert.equal((await preparePlanning(input)).rollover.status,'complete');
  await assert.rejects(savePlanningState(stateInput),/state changed/);
  await writeFile(plan,(await readFile(plan,'utf8')).replace('type: daily-plan','type: task'));
  await assert.rejects(preparePlanning(input),/Invalid daily-plan identity/);
});

test('preparation cannot complete pending carry or unresolved current rows', async () => {
  const input = await fixture();
  const config = path.join(input.vaultRoot,'.nyssaai/daily-tasks');
  await mkdir(config,{recursive:true});
  await writeFile(path.join(config,'profile.json'),JSON.stringify({schema_version:1,user:{name:'Owner',email:owner},
    timezone:input.timezone,priorities:[],vaultRoot:'./',projectsRoot:'./1-projects',dailyPlansRelative:'2-areas/daily-plans'}));
  await writeFile(path.join(input.dailyPlansRoot,'2026.10.05-daily-plan.md'),`---\nid: ${id(22)}\ntype: daily-plan\n---\n- [ ] [[../../1-projects/2026.01.01-alpha/first/a|A]] <!-- ref: ${id(3)} -->\n`);
  const today = path.join(input.dailyPlansRoot,'2026.10.06-daily-plan.md');
  await writeFile(today,`---\nid: ${id(21)}\ntype: daily-plan\n---\n`);
  const prepared = await preparePlanning(input);
  assert.equal(prepared.rollover.own.length,1);
  await assert.rejects(savePlanningState({...input,action:'complete-rollover',expectedPlanHash:prepared.current.sha256,
    expectedPreviousHash:prepared.previous.sha256,expectedStateHash:null,expectedInventoryHash:prepared.inventoryHash}),/pending membership/);
  await writeFile(today,(await readFile(today,'utf8'))+'- [ ] candidate\n');
  const candidate = await preparePlanning(input);
  await assert.rejects(savePlanningState({...input,action:'save-review',expectedPlanHash:candidate.current.sha256,
    expectedPreviousHash:candidate.previous.sha256,expectedStateHash:null,expectedInventoryHash:candidate.inventoryHash,expectedReviewHash:candidate.reviewHash}),/missing or duplicate/);
});

test('valid tasks and future allocations survive an invalid ancestor, while additions stay blocked', async () => {
  const input = await fixture();
  const index = path.join(input.project,'project-index.md');
  await writeFile(index,(await readFile(index,'utf8')).replace('project-state: not-started','project-state: paused'));
  const {inventory} = await projectInventory(input);
  assert.equal(inventory.tasks.length,3);
  assert.equal(inventory.tasks.find(t => t.id === id(4)).planned[0].date,'2026.10.07');
  assert.equal(planningReview({inventory,userEmail:owner,timezone:input.timezone,now}).available.length,0);
});

test('inventory uses agreed shape, table order and one planned source, then reuses and invalidates', async () => {
  const input = await fixture();
  const cold = await projectInventory(input);
  assert.equal(cold.status,'rebuilt');
  assert.deepEqual(Object.keys(cold.inventory),['schemaVersion','generatedAt','scope','projects','milestones','tasks','blockers','sources','diagnostics']);
  assert.deepEqual(cold.inventory.tasks.map(t => t.id),[id(3),id(4),id(6)]);
  assert.deepEqual(cold.inventory.tasks[1].planned,[{date:'2026.10.07',source:'2-areas/daily-plans/2026.10.07-daily-plan.md'}]);
  assert.ok(cold.inventory.sources.every(s => !path.isAbsolute(s.path)));
  const reuse = await projectInventory({...input,now:'2026-10-06T15:00:00Z'});
  assert.equal(reuse.status,'reused');
  assert.equal(reuse.metrics.sourceReads,0);
  const view = planningReview({inventory:reuse.inventory,userEmail:owner,timezone:input.timezone,now});
  assert.deepEqual(view.available.map(t => t.id),[id(3)]);
  assert.deepEqual(view.counts,{openProjects:1,openTasks:3,lateTasks:3});
  await unlink(input.future);
  const changed = await projectInventory({...input,now:'2026-10-06T15:10:00Z'});
  assert.equal(changed.status,'rebuilt');
  assert.equal(changed.inventory.tasks[1].planned.length,0);
  assert.equal((await projectInventory({...input,now:'2026-10-06T19:10:00Z'})).status,'rebuilt');
  assert.equal((await projectInventory({...input,forceRefresh:true})).status,'rebuilt');
  const preview = await projectInventory({...input,dryRun:true,forceRefresh:true});
  assert.equal(preview.status,'preview');
  assert.equal(JSON.parse(await readFile(cold.path,'utf8')).generatedAt,now);
});

test('conflicting active dates are diagnosed, historical selections do not conflict, move is a proposal', async () => {
  const input = await fixture();
  const plan = date => path.join(input.dailyPlansRoot,`${date}-daily-plan.md`);
  const row = `- [ ] [[task|B]] <!-- ref: ${id(4)} -->\n`;
  await writeFile(plan('2026.10.05'),row);
  let result = await projectInventory(input);
  assert.equal(result.inventory.tasks[1].planned.length,1);
  const proposed = planSelection({inventory:result.inventory,taskIds:[id(4)],action:'move',date:'2026.10.08',today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot});
  assert.equal(proposed.effects[0].from.date,'2026.10.07');
  assert.equal(proposed.effects[0].to.date,'2026.10.08');
  assert.equal(proposed.effects[0].to.createIfMissing,true);
  assert.equal(planSelection({inventory:result.inventory,taskIds:[id(4)],action:'add',date:'2026.10.08',today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot}).conflicts.length,1);
  await writeFile(plan('2026.10.08'),row);
  result = await projectInventory({...input,forceRefresh:true});
  assert.ok(result.inventory.diagnostics.some(d => d.code === 'multiple-planning-dates' && d.recordId === id(4)));
  assert.equal(result.inventory.tasks[1].planned.length,0);
  assert.ok(!planningReview({inventory:result.inventory,userEmail:owner,timezone:input.timezone,now,allMilestones:true}).available.some(t => t.id === id(4)));
});

test('review pages keep stable handles, preserve later selections, owner filtering and day calculations', async () => {
  const input = await fixture();
  const {inventory} = await projectInventory(input);
  const task = inventory.tasks[0];
  inventory.tasks = Array.from({length:18},(_,n) => ({...task,id:id(n+30),assignee:'agent',planned:[]}));
  inventory.tasks.push({...task,id:id(70),milestoneId:id(5),planned:[]});
  let screen = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,selected:[{id:id(70),carriedFrom:'2026.10.05'}]});
  assert.equal(screen.selected[0].number,1);
  assert.equal(screen.available.length,15);
  const next = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,selected:[{id:id(70),carriedFrom:'2026.10.05'}],page:1,mapping:screen.mapping});
  assert.deepEqual(next.available.map(t => t.number),[17,18,19]);
  assert.equal(next.selected[0].carriedFrom,'2026.10.05');
  assert.equal(maintenanceStatus({now,lastFullReconcileAt:'2026-10-06T10:00:00Z'}).fullReconcileDue,true);
  assert.equal(maintenanceStatus({now,lastFullReconcileAt:'2026-10-06T11:00:00Z'}).fullReconcileDue,false);
});

test('project order uses dates then names and failed refresh preserves prior cache', async () => {
  const input = await fixture();
  for (const [n,name] of [[100,'zeta'],[101,'beta'],[102,'2025.01.01-older']]) {
    const dir = path.join(input.projectsRoot,name); await mkdir(dir);
    await writeFile(path.join(dir,'project-index.md'),doc(n,'project',name));
  }
  const result = await projectInventory(input);
  assert.deepEqual(result.inventory.projects.map(p => p.title),['2025.01.01-older','Alpha','beta','zeta']);
  await writeFile(input.future,'- [ ] unidentified future task\n');
  const uncertain = await projectInventory({...input,forceRefresh:true});
  assert.ok(uncertain.inventory.diagnostics.some(d => d.code === 'selection-identity'));
  assert.equal(planningReview({inventory:uncertain.inventory,userEmail:owner,timezone:input.timezone,now}).available.length,0);
  const before = await readFile(result.path,'utf8');
  await assert.rejects(projectInventory({...input,ttlSeconds:-1}),/ttlSeconds/);
  assert.equal(await readFile(result.path,'utf8'),before);
  // A non-file dated plan fails refresh after a successful cache, without advancing it.
  await mkdir(path.join(input.dailyPlansRoot,'2026.10.09-daily-plan.md'));
  await assert.rejects(projectInventory({...input,forceRefresh:true,now:'2026-10-06T16:00:00Z'}),/must be a file/);
  assert.equal(await readFile(result.path,'utf8'),before);
});

test('local midnight expires date-sensitive allocations even within the TTL', async () => {
  const input = await fixture();
  await writeFile(path.join(input.dailyPlansRoot,'2026.10.06-daily-plan.md'),`- [ ] Task <!-- ref: ${id(4)} -->\n`);
  const before = await projectInventory({...input,now:'2026-10-07T04:50:00Z'});
  assert.ok(before.inventory.diagnostics.some(d => d.code === 'multiple-planning-dates'));
  const after = await projectInventory({...input,now:'2026-10-07T05:10:00Z'});
  assert.equal(after.status,'rebuilt');
  assert.deepEqual(after.inventory.tasks[1].planned,[{date:'2026.10.07',source:'2-areas/daily-plans/2026.10.07-daily-plan.md'}]);
  assert.ok(!after.inventory.diagnostics.some(d => d.code === 'multiple-planning-dates'));
  await assert.rejects(projectInventory({...input,dailyPlansRoot:path.dirname(input.vaultRoot)}),/beneath vaultRoot/);
});

test('invalidation, corrupt cache and failed sidecar read preserve truthful freshness', async () => {
  const input = await fixture();
  const cold = await projectInventory(input);
  await invalidateInventory({...input,dryRun:true});
  assert.equal((await projectInventory(input)).status,'reused');
  await invalidateInventory(input);
  assert.equal((await projectInventory(input)).status,'rebuilt');
  await writeFile(cold.path,'{broken');
  assert.equal((await projectInventory(input)).status,'rebuilt');
  const before = await readFile(cold.path,'utf8');
  const sidecar = path.join(path.dirname(cold.path),'project-index-freshness.json');
  await unlink(sidecar); await mkdir(sidecar);
  await assert.rejects(projectInventory({...input,forceRefresh:true,now:'2026-10-06T16:00:00Z'}));
  assert.equal(await readFile(cold.path,'utf8'),before);
});

test('selected rows retain allocation, terminal work and out-of-view responsibility', async () => {
  const input = await fixture();
  const {inventory} = await projectInventory(input);
  const canonical = {id:id(4),project_id:id(1),milestone_id:id(2),owner,state:'not-started',title:'B'};
  const completed = {...canonical,id:id(80),state:'completed'};
  inventory.tasks.push({...inventory.tasks[0],id:id(90),owner:'someone@example.test'});
  const screen = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,
    selected:[{id:id(4)},{id:id(80)},{id:id(90)}],selectedRecords:[canonical,completed]});
  assert.deepEqual(screen.selected[0].planned,inventory.tasks[1].planned);
  assert.equal(screen.selected[1].state,'completed');
  assert.deepEqual(screen.outOfViewSelectedIds,[id(90)]);
  assert.equal(carryForward([{id:id(4)}],[canonical],owner,{inventory,today:'2026.10.06'}).own.length,0);
  inventory.milestones[0].state = 'completed';
  const all = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,allMilestones:true});
  assert.deepEqual(all.available.map(t => t.id),[id(6)]);
});

test('manual future status edits remain affected work until reconciled, notes are not allocations', async () => {
  const input = await fixture();
  for (const mark of ['x','-']) {
    await writeFile(input.future,`- [${mark}] [[task|B]] <!-- ref: ${id(4)} -->\n`);
    const {inventory} = await projectInventory({...input,forceRefresh:true});
    assert.ok(inventory.diagnostics.some(d => d.code === 'view-state-difference' && d.recordId === id(4)));
    const view = planningReview({inventory,userEmail:owner,timezone:input.timezone,now});
    assert.ok(!view.available.some(task => task.id === id(4)));
    assert.equal(planSelection({inventory,taskIds:[id(4)],action:'move',date:'2026.10.08',today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot}).effects.length,0);
    assert.equal(carryForward([{id:id(4)}],[{id:id(4),state:'not-started',owner}],owner,{inventory,today:'2026.10.06'}).unresolved[0].reason,'view-needs-reconciliation');
  }
  await writeFile(input.future,`| Reference | Context |\n| --- | --- |\n| [[task\\|B]] <!-- ref: ${id(4)} --> | Reference only |\n`);
  const {inventory} = await projectInventory({...input,forceRefresh:true});
  assert.equal(inventory.tasks[1].planned.length,0);
  assert.equal(inventory.diagnostics.length,0);
  assert.ok(planningReview({inventory,userEmail:owner,timezone:input.timezone,now}).available.some(task => task.id === id(4)));
});

test('removal preserves date intent, repeated selections are no-ops and carry conflicts isolate tasks', async () => {
  const input = await fixture();
  const {inventory} = await projectInventory(input);
  const command = {inventory,taskIds:[id(4)],today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot};
  assert.equal(planSelection({...command,action:'remove'}).conflicts[0].reason,'selection-date-changed');
  const remove = planSelection({...command,action:'remove',date:'2026.10.07'});
  assert.equal(remove.effects[0].from.date,'2026.10.07');
  assert.equal(remove.effects[0].to,null);
  assert.deepEqual(planSelection({...command,action:'add',date:'2026.10.07'}),{effects:[],conflicts:[]});
  assert.deepEqual(planSelection({...command,taskIds:[id(3)],action:'remove'}),{effects:[],conflicts:[]});
  const rows = [{id:id(3)},{id:id(4)}], records = rows.map(row => ({...row,owner,state:'not-started'}));
  for (const [code,reason] of [['selection-identity','ambiguous-active-selection'],['multiple-planning-dates','multiple-planning-dates']]) {
    inventory.diagnostics = [{code,recordId:id(4)}];
    inventory.tasks[1].planned = [];
    const carried = carryForward(rows,records,owner,{inventory,today:'2026.10.06'});
    assert.deepEqual(carried.own.map(row => row.id),[id(3)]);
    assert.equal(carried.unresolved[0].reason,reason);
  }
});

test('invalid ancestor text blocks affected additions uniformly, preserving selections and unrelated projects', async () => {
  const input = await fixture();
  const milestonePath = path.join(input.project,'first/milestone.md');
  const original = await readFile(milestonePath,'utf8');
  const unrelated = path.join(input.projectsRoot,'beta');
  await mkdir(path.join(unrelated,'release'),{recursive:true});
  await writeFile(path.join(unrelated,'project-index.md'),doc(100,'project','Beta','',
    `- [ ] [[release/milestone|Release]] <!-- ref: ${id(101)} -->\n- [ ] [[release/prepare-budget|Prepare budget]] <!-- ref: ${id(102)} -->`));
  await writeFile(path.join(unrelated,'release/milestone.md'),doc(101,'milestone','Release',`project_id: ${id(100)}\n`));
  await writeFile(path.join(unrelated,'release/prepare-budget.md'),doc(102,'task','Prepare budget',`project_id: ${id(100)}\nmilestone_id: ${id(101)}\n`));
  const cases = [
    [original.replace('milestone-state: not-started','milestone-state: paused'),'invalid-state'],
    [original.replace('title: "First"','title: ""').replace('# First','# '),'missing-title'],
    [original.replace(`owner: ${owner}`,'owner: agent'),'invalid-owner'],
    [original.replace(`created_at: ${now}`,'created_at: invalid'),'invalid-time'],
    [original.replace('---\n# First','assignee: ""\n---\n# First'),'invalid-assignee'],
    [original.replace('type: milestone','type: milsetone'),'invalid-type'],
    [original.replace(`project_id: ${id(1)}`,`project_id: ${id(999)}`),'missing-reference'],
    [original.replace('---\n# First','nested:\n  field: value\n---\n# First'),'invalid-frontmatter'],
    [original.replace(`id: ${id(2)}\n`,'').replace(`project_id: ${id(1)}\n`,''),'invalid-id'],
  ];
  for (const [text,code] of cases) {
    await writeFile(milestonePath,text);
    const {inventory} = await projectInventory({...input,forceRefresh:true});
    assert.ok(inventory.diagnostics.some(d => d.code === code),code);
    assert.ok(inventory.diagnostics.some(d => d.code === 'invalid-planning-scope' && d.projectId === id(1)),code);
    const blockedSelection = planSelection({inventory,taskIds:[id(6)],action:'add',date:'2026.10.06',today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot});
    assert.equal(blockedSelection.effects.length,0,code);
    assert.equal(blockedSelection.conflicts.length,1,code);
    for (const allMilestones of [false,true]) {
      const review = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,selected:[{id:id(3)}],allMilestones});
      assert.deepEqual(review.available.map(t => t.id),[id(102)],code);
      assert.equal(review.selected[0].id,id(3),code);
      assert.equal(review.incomplete,true,code);
    }
  }
  await writeFile(milestonePath,original);
  await writeFile(path.join(input.project,'first/duplicate.md'),original);
  const duplicate = await projectInventory({...input,forceRefresh:true});
  assert.deepEqual(planningReview({inventory:duplicate.inventory,userEmail:owner,timezone:input.timezone,now}).available.map(t => t.id),[id(102)]);
  await unlink(path.join(input.project,'first/duplicate.md'));
  const fixed = await projectInventory({...input,forceRefresh:true});
  assert.deepEqual(planningReview({inventory:fixed.inventory,userEmail:owner,timezone:input.timezone,now}).available.map(t => t.id),[id(3),id(102)]);
});

test('invalid task metadata isolates that task without blocking other tasks or hiding a selection', async () => {
  const input = await fixture();
  const taskPath = path.join(input.project,'first/a.md');
  await writeFile(taskPath,(await readFile(taskPath,'utf8')).replace(`owner: ${owner}`,'owner: invalid'));
  await unlink(input.future);
  const {inventory} = await projectInventory(input);
  const review = planningReview({inventory,userEmail:owner,timezone:input.timezone,now,selected:[{id:id(3)}]});
  assert.deepEqual(review.available.map(t => t.id),[id(4)]);
  assert.equal(review.selected[0].unresolved,true);
});

test('accepted independent projects storage indexes through a logical anchor without absolute cache paths', async () => {
  const input = await fixture();
  const root = await realpath(await mkdtemp(path.resolve('.temp/external-projects-')));
  const projectsRoot = path.join(root,'projects'), homeRoot = path.join(root,'home');
  await mkdir(homeRoot);
  await cp(input.projectsRoot,projectsRoot,{recursive:true});
  const configRoot = path.join(input.vaultRoot,'.nyssaai/daily-tasks');
  await mkdir(configRoot,{recursive:true});
  await writeFile(path.join(configRoot,'profile.json'),JSON.stringify({schema_version:1,
    user:{name:'Example',email:owner},timezone:input.timezone,priorities:[],vaultRoot:'.',projectsRoot,dailyPlansRelative:'2-areas/daily-plans'}));
  const context = await resolveContext({vaultRoot:input.vaultRoot,homeRoot,now});
  const cold = await projectInventory(context);
  assert.equal(cold.inventory.scope.projectsRoot,'@projectsRoot');
  assert.deepEqual(cold.inventory.tasks.map(task => task.id),[id(3),id(4),id(6)]);
  assert.equal(cold.planningBinding,context.planningBinding);
  const cache = await readFile(cold.path,'utf8');
  assert.ok(!cache.includes(JSON.stringify(root).slice(1,-1)));
  assert.ok(cold.inventory.sources.every(source => !path.isAbsolute(source.path)));
  const warm = await projectInventory(context);
  assert.equal(warm.status,'reused');
  assert.equal(warm.metrics.sourceReads,0);
  const review = planningReview({...context,inventory:warm.inventory,userEmail:owner,
    contextBinding:context.planningBinding,inventoryBinding:warm.planningBinding});
  assert.deepEqual(review.available.map(task => task.id),[id(3)]);
});

test('planning rejects another vault inventory, destination roots or numbered screen even with matching task IDs', async () => {
  const first = await fixture(), second = await fixture();
  const a = await projectInventory(first), b = await projectInventory(second);
  const request = {...first,inventory:a.inventory,userEmail:owner,
    contextBinding:planningBinding(first),inventoryBinding:a.planningBinding};
  const screen = planningReview(request);
  assert.equal(screen.mappingBinding,request.contextBinding);
  assert.throws(() => planningReview({...request,inventory:b.inventory,inventoryBinding:b.planningBinding}),/Inventory binding differs/);
  assert.throws(() => planningReview({...request,mapping:screen.mapping,mappingBinding:b.planningBinding}),/different vault binding/);
  assert.throws(() => planSelection({...request,taskIds:[id(3)],action:'add',date:'2026.10.06',today:'2026.10.06',dailyPlansRoot:second.dailyPlansRoot}),/roots differ/);
  assert.deepEqual(planningReview({...request,mapping:screen.mapping,mappingBinding:screen.mappingBinding}).mapping,screen.mapping);
});

test('following-line selections are allocated and legacy future cancellation reaches reconciliation', async () => {
  const input = await fixture();
  const reference = `  <!-- ref: ${id(4)} -->`;
  await writeFile(input.future,`- [ ] [[task|B]]\n${reference}\n`);
  const active = await projectInventory(input);
  assert.equal(active.inventory.tasks[1].planned[0].date,'2026.10.07');
  assert.deepEqual(planningReview({inventory:active.inventory,userEmail:owner,timezone:input.timezone,now}).available.map(task => task.id),[id(3)]);
  await writeFile(input.future,`- [ ] ~~[[task|B]]~~ Cancelled\n${reference}\n`);
  const edited = await projectInventory(input);
  assert.ok(edited.inventory.diagnostics.some(d => d.code === 'view-state-difference' && d.recordId === id(4)));
  assert.ok(!planningReview({inventory:edited.inventory,userEmail:owner,timezone:input.timezone,now}).available.some(task => task.id === id(4)));
  assert.equal(planSelection({inventory:edited.inventory,taskIds:[id(4)],action:'add',date:'2026.10.06',today:'2026.10.06',dailyPlansRoot:input.dailyPlansRoot}).effects.length,0);
  // Project list projections normalize the same legacy state before any view rewrite.
  await unlink(input.future);
  const index = path.join(input.project,'project-index.md');
  await writeFile(index,(await readFile(index,'utf8')) + `\n- [ ] ~~[[first/b|B]]~~ Cancelled <!-- ref: ${id(4)} -->\n`);
  const projectEdit = await projectInventory(input);
  assert.ok(projectEdit.inventory.diagnostics.some(d => d.code === 'view-state-difference' && d.recordId === id(4)));
});
