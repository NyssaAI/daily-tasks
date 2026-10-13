import test from 'node:test';
import assert from 'node:assert/strict';
import { planningReview } from '../lib/planning/review.mjs';

test('four projects keep three ordered options per page from only the lowest incomplete milestone', () => {
  const inventory = {schemaVersion:1,projects:[],milestones:[],tasks:[],diagnostics:[]};
  for (let p = 1; p <= 4; p++) {
    inventory.projects.push({id:`p${p}`,state:'not-started'});
    for (let m = 1; m <= 3; m++) {
      inventory.milestones.push({id:`p${p}m${m}`,projectId:`p${p}`,state:'not-started'});
      for (let t = 1; t <= 3; t++) inventory.tasks.push({id:`p${p}m${m}t${t}`,projectId:`p${p}`,milestoneId:`p${p}m${m}`,state:'not-started',planned:[]});
    }
  }
  const input = {inventory,userEmail:'alex@example.test',timezone:'UTC',now:'2026-10-13T12:00:00Z'};
  let mapping;
  for (let page = 0; page < 4; page++) {
    const review = planningReview({...input,page,mapping,allMilestones:true});
    assert.deepEqual(review.available.map(t => t.id),[1,2,3].map(t => `p${page+1}m1t${t}`));
    assert.deepEqual(review.available.map(t => t.number),[1,2,3].map(t => page*3+t));
    assert.equal(review.pageCount,4);
    assert.equal(review.hasMore,page < 3);
    assert.equal(review.counts.openTasks,36);
    mapping = review.mapping;
  }
  const previous = planningReview({...input,page:1,mapping});
  assert.deepEqual(previous.available.map(t => t.number),[4,5,6]);
  assert.deepEqual(previous.selected,[]);
  assert.deepEqual(previous.mapping,mapping);
  inventory.milestones[0].state = 'completed';
  assert.deepEqual(planningReview(input).available.map(t => t.id),[1,2,3].map(t => `p1m2t${t}`));
  inventory.tasks = inventory.tasks.filter(t => t.milestoneId !== 'p1m2');
  assert.ok(planningReview(input).available.every(t => t.projectId !== 'p1'));
});

test('review resumes by project identity, advances through saved order and retains completion', () => {
  const inventory = {schemaVersion:1,diagnostics:[],projects:[],milestones:[],tasks:[]};
  for (const n of [1,2,3,4]) {
    inventory.projects.push({id:`p${n}`,state:'not-started'});
    inventory.milestones.push({id:`m${n}`,projectId:`p${n}`,state:'not-started'});
    inventory.tasks.push({id:`t${n}`,projectId:`p${n}`,milestoneId:`m${n}`,state:'not-started',planned:[]});
  }
  const input = {inventory,userEmail:'alex@example.test',timezone:'UTC',now:'2026-10-13T12:00:00Z'};
  const original = planningReview({...input,page:1});
  const resume = {position:original.position,mapping:original.mapping};
  inventory.tasks[0].state = 'completed';
  const shifted = planningReview({...input,...resume});
  assert.equal(shifted.page,0);
  assert.equal(shifted.position.projectId,'p2');
  assert.equal(shifted.available[0].number,2);
  inventory.tasks[1].state = 'completed';
  inventory.tasks[2].state = 'cancelled';
  const advanced = planningReview({...input,...resume});
  assert.equal(advanced.position.projectId,'p4');
  assert.equal(advanced.available[0].number,4);
  inventory.tasks[0].state = 'not-started';
  inventory.tasks[3].state = 'completed';
  const complete = planningReview({...input,...resume});
  assert.equal(complete.reviewComplete,true);
  assert.deepEqual(complete.available,[]);
  assert.equal(planningReview({...input,position:complete.position}).reviewComplete,true);
  assert.equal(planningReview({...input,position:complete.position,page:0}).position.projectId,'p1');
  assert.equal(planningReview({...input,mapping:original.mapping}).available[0].number,1);
});
