import test from 'node:test';
import assert from 'node:assert/strict';
import { planRollover } from '#core/planning/planning.mjs';

const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12,'0')}`;
const userEmail = 'owner@example.test';
const today = '2026.10.07', previousDate = '2026.10.06', planId = id(20);
const open = n => ({id:id(n),owner:userEmail,state:'not-started'});

test('in-progress work carries without a previous selection until terminal or allocated later', () => {
  const records = [
    {...open(1),state:'in-progress',title:'Started work'},
    {...open(2),state:'in-progress',assignee:'research-agent'},
    {...open(3),state:'in-progress',owner:'someone@example.test'},
    {...open(4),state:'completed'}, {...open(5),state:'cancelled'},
    {...open(6),state:'in-progress'}, open(7)
  ];
  const inventory = {tasks:records.map(record => ({...record,planned:record.id === id(6) ? [{date:'2026.10.09'}] : []})),diagnostics:[]};
  const request = {today,planId,userEmail,records,inventory};
  const result = planRollover(request);
  assert.deepEqual(result.selected.map(row => row.id),[id(1),id(2),id(3)]);
  assert.equal(result.own[0].carriedFrom,undefined,'No invented previous-plan provenance');
  assert.equal(result.delegated[0].id,id(2));
  assert.equal(result.followUp[0].id,id(3));
  const next = planRollover({...request,today:'2026.10.08',planId:id(21),previousDate:today,previousRows:result.selected});
  assert.deepEqual(next.selected.map(row => row.id),[id(1),id(2),id(3)]);
  assert.equal(next.own[0].carriedFrom,today);
  const rescheduledDay = planRollover({...request,today:'2026.10.09',planId:id(22)});
  assert.ok(rescheduledDay.selected.some(row => row.id === id(6)));
});

test('old deselections cannot drop in-progress work from the next plan', () => {
  const records = [1,2,3].map(n => ({...open(n),state:'in-progress'}));
  const result = planRollover({today,previousDate,planId,userEmail,records,
    previousRows:[{id:id(1),selected:false},{id:id(2)}],currentRows:[{id:id(3),selected:false}],
    removedIds:[id(2),id(3)]});
  assert.deepEqual(result.selected.map(row => row.id),[id(1),id(2),id(3)]);
});

test('rollover merges yesterday into a pre-created plan while preserving future, terminal and removed work', () => {
  const records = [open(1),open(2),open(3),{...open(4),state:'completed'},open(5),{...open(6),assignee:'research-agent'},{...open(7),owner:'someone@example.test'}];
  const currentRows = [{id:id(2),title:'Already selected B',customNote:'retain this edit'}];
  const previousRows = records.map(record => ({id:record.id,selected:record.id !== id(5)}));
  const inventory = {tasks:records.map(record => ({id:record.id,planned:record.id === id(3) ? [{date:'2026.10.08'}] : []})),diagnostics:[]};
  const input = {today,previousDate,planId,userEmail,records,currentRows,previousRows,inventory};
  const before = structuredClone(input);
  const proposal = planRollover(input);
  assert.equal(proposal.status,'due');
  assert.deepEqual(proposal.selected.map(row => row.id),[id(2),id(1),id(6),id(7)]);
  assert.deepEqual(proposal.selected[0],currentRows[0]);
  assert.equal(proposal.own[0].carriedFrom,previousDate);
  assert.equal(proposal.delegated[0].carriedFrom,previousDate);
  assert.equal(proposal.followUp[0].carriedFrom,previousDate);
  assert.deepEqual(proposal.unresolved,[]);
  assert.deepEqual(input,before);
});

test('verified daily completion preserves a later removal and does not carry a second time', () => {
  const state = {schemaVersion:1,date:today,planId,operationId:id(30),completedAt:'2026-10-07T14:00:00Z'};
  const input = {today,previousDate,planId,userEmail,records:[open(1),open(2)],
    currentRows:[{id:id(2)}],previousRows:[{id:id(1)},{id:id(2)}],state};
  const repeated = planRollover(input);
  assert.equal(repeated.status,'complete');
  assert.deepEqual(repeated.selected,[{id:id(2)}]);
  assert.deepEqual(repeated.own,[]);
  // A current-day state file is checked independently of the old source rows.
  assert.equal(planRollover({today,planId,userEmail,currentRows:input.currentRows,state}).status,'complete');
  for (const change of [{planId:id(21)},{date:previousDate},{completedAt:'invalid'},{operationId:null}]) {
    const conflict = planRollover({...input,state:{...state,...change}});
    assert.equal(conflict.status,'conflict');
    assert.deepEqual(conflict.selected,input.currentRows);
    assert.deepEqual(conflict.own,[]);
  }
});

test('rollover preserves unresolved identities and explicit removals during unfinished recovery', () => {
  const input = {today,previousDate,planId,userEmail,records:[open(1),open(2)],
    currentRows:[{id:id(2),selected:false},{title:'Current unidentified selection'}],
    previousRows:[{id:id(1)},{id:id(2)},{id:id(99)},{title:'Previous unidentified selection'}],removedIds:[id(1)]};
  const result = planRollover(input);
  assert.deepEqual(result.own,[]);
  assert.deepEqual(result.unresolved.map(row => row.reason),['missing-record','missing-identity']);
  assert.equal(result.selected.length,3);
  assert.ok(!result.selected.some(row => [id(1),id(2)].includes(row.id)));
  const pending = planRollover({...input,removedIds:[],state:{schemaVersion:1,date:today,planId,removedIds:[id(1)]}});
  assert.equal(pending.status,'due');
  assert.deepEqual(pending.own,[]);
  assert.throws(() => planRollover({...input,removedIds:['unknown']}),/required/);
  assert.throws(() => planRollover({...input,previousDate:today}),/required/);
  const invalid = planRollover({...input,removedIds:[],records:[{...open(1),state:'in progess'},open(2)]});
  assert.equal(invalid.unresolved[0].reason,'invalid-record');
});
