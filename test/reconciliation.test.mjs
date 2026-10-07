import test from 'node:test';
import assert from 'node:assert/strict';
import { reconcileRecord, reopenAncestors, recoverOperation } from '../lib/reconciliation/reconciliation.mjs';
import { parseChecklist } from '../lib/planning/planning.mjs';
const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12, '0')}`;

test('stale checkbox never reopens changed task; independent edits merge', () => {
  const base = {id:id(1), type:'task', state:'not-started', title:'Old'};
  const current = {...base, state:'completed'};
  const result = reconcileRecord(base, current, [{id:id(1), checked:false, title:'New'}]);
  assert.equal(result.record.state, 'completed');
  assert.equal(result.record.title, 'New');
  assert.deepEqual(result.conflicts, []);
});

test('conflicts preserve current facts and do not block independent changes', () => {
  const base = {id:id(1), type:'task', state:'not-started', title:'Old'};
  const result = reconcileRecord(base, {...base, state:'cancelled'}, [{id:id(1), checked:true, title:'New'}]);
  assert.equal(result.conflicts[0].field, 'state');
  assert.equal(result.record.state, 'cancelled');
  assert.equal(result.record.title, 'New');
  assert.throws(() => reconcileRecord(base, base, [{id:id(99), checked:true}]));
});

test('unchecking completed task restores start-aware state and records are not mutated', () => {
  const base = {id:id(1), type:'task', state:'completed', started_at:'2026-10-05T10:00:00Z'};
  assert.equal(reconcileRecord(base, base, [{id:id(1), checked:false}]).record.state, 'in-progress');
  assert.equal(base.state, 'completed');
  delete base.started_at;
  assert.equal(reconcileRecord(base, base, [{id:id(1), checked:false}]).record.state, 'not-started');
});

test('DoD and blockers reopen parents while preserving completed tasks', () => {
  const records = [{id:id(1),type:'project',state:'completed'},
    {id:id(2),type:'milestone',state:'completed',project_id:id(1)},
    {id:id(3),type:'task',state:'completed',milestone_id:id(2),project_id:id(1)},
    {id:id(4),type:'blocker',state:'open',blocks:[id(3)]}];
  const result = reopenAncestors(records, [id(4)]);
  assert.equal(result.records[0].state, 'in-progress');
  assert.equal(result.records[1].state, 'in-progress');
  assert.equal(result.records[2].state, 'completed');
  assert.equal(records[0].state, 'completed');
  assert.deepEqual(new Set(result.changedIds), new Set([id(1),id(2)]));
});

test('recovery compares expected values and never infers ambiguous intent', () => {
  const operation = {changes:[{key:'task',before:{present:true,value:'open'},after:{present:true,value:'done'}}, {key:'index',before:{present:true,value:false},after:{present:true,value:true}}]};
  const partial = recoverOperation(operation, {task:'done',index:false});
  assert.equal(partial.status, 'pending');
  assert.equal(partial.pending.length, 1);
  assert.equal(recoverOperation(operation, {task:'done',index:true}).status, 'already-applied');
  assert.equal(recoverOperation(operation, {task:'cancelled',index:false}).status, 'conflict');
});

test('reopening isolates unrelated copied IDs and rejects ambiguity in affected records', () => {
  const records = [{id:id(1),type:'project',state:'completed'},
    {id:id(2),type:'milestone',state:'completed',project_id:id(1)},
    {id:id(3),type:'task',state:'in-progress',milestone_id:id(2)},
    {id:id(4),type:'project',state:'completed'},
    {id:id(4),type:'project',state:'completed'}];
  const result = reopenAncestors(records,[id(3)]);
  assert.deepEqual(new Set(result.changedIds),new Set([id(1),id(2)]));
  assert.deepEqual(result.records.slice(3),records.slice(3));
  assert.throws(() => reopenAncestors(records,[id(4)]),/Duplicate record identity/);
  assert.throws(() => reopenAncestors([...records,{...records[1]}],[id(3)]),/Duplicate record identity/);
  const blocker = {id:id(5),type:'blocker',state:'open',blocks:[id(4)]};
  assert.throws(() => reopenAncestors([...records,blocker],[id(5)]),/Duplicate record identity/);
  assert.equal(records[0].state,'completed');
});

test('invalid metadata and blocker checkbox states are handled by record type', () => {
  const base = {id:id(1),type:'blocker',state:'open',owner:'owner@example.test'};
  const result = reconcileRecord(base, base, [{id:id(1),checked:true,owner:'not-email'}]);
  assert.equal(result.record.state,'resolved');
  assert.equal(result.record.owner,base.owner);
  assert.equal(result.conflicts[0].field,'owner');
});

test('reopening clears present resolution timestamp, retaining baseline history', () => {
  const base = {id:id(1),type:'task',state:'completed',resolved_at:'2026-10-05T12:00:00Z'};
  const result = reconcileRecord(base,base,[{id:id(1),checked:false}]);
  assert.equal(result.record.resolved_at,undefined);
  assert.equal(base.resolved_at,'2026-10-05T12:00:00Z');
});

test('recovery snapshots survive JSON for absent fields and timestamp removal', () => {
  const base = {id:id(1),type:'task',state:'completed',resolved_at:'2026-10-05T12:00:00Z'};
  const result = JSON.parse(JSON.stringify(reconcileRecord(base,base,[{id:id(1),checked:false,target_date:'2026-10-06T12:00:00Z'}])));
  const operation = {changes:result.changes.map(({field,...change}) => ({key:field,...change}))};
  assert.equal(recoverOperation(operation,base).status,'pending');
  assert.equal(recoverOperation(operation,result.record).status,'already-applied');
  assert.deepEqual(operation.changes.find(c => c.key === 'resolved_at').after,{present:false});
  assert.deepEqual(operation.changes.find(c => c.key === 'target_date').before,{present:false});
});

test('explicit null removes optional assignment and target while preserving owner', () => {
  const base = {id:id(1),type:'task',state:'not-started',owner:'owner@example.test',assignee:'agent',target_date:'2026-10-05T12:00:00Z'};
  const result = reconcileRecord(base,base,[{id:id(1),assignee:null,target_date:null}]);
  assert.equal(Object.hasOwn(result.record,'assignee'),false);
  assert.equal(Object.hasOwn(result.record,'target_date'),false);
  assert.equal(result.record.owner,base.owner);
});

test('parsed explicit status edits override checkbox reopening inference', () => {
  const base = {id:id(1),type:'task',state:'completed'};
  for (const [mark,state] of [['-','cancelled'],['>','in-progress']]) {
    const [row] = parseChecklist(`- [${mark}] [[task|Work]] <!-- ref: ${id(1)} -->`);
    const result = reconcileRecord(base,base,[{id:row.id,checked:row.checked,state:row.state}]);
    assert.deepEqual(result.conflicts,[]);
    assert.equal(result.record.state,state);
  }
  assert.throws(() => reconcileRecord(base,base,[{id:id(1),checked:true,state:'cancelled'}]),/disagree/);
  const blocker = {id:id(2),type:'blocker',state:'open'};
  assert.equal(reconcileRecord(blocker,blocker,[{id:id(2),checked:true,state:'resolved'}]).record.state,'resolved');
});

test('legacy cancellation reconciles as a state edit and never overrides changed canonical facts', () => {
  const base = {id:id(1),type:'task',state:'not-started'};
  const [row] = parseChecklist(`- [ ] ~~[[task|Work]]~~ Cancelled\n  <!-- ref: ${id(1)} -->`);
  const view = {id:row.id,state:row.state,checked:row.checked};
  const changed = reconcileRecord(base,base,[view]);
  assert.equal(changed.record.state,'cancelled');
  assert.deepEqual(changed.conflicts,[]);
  const conflict = reconcileRecord(base,{...base,state:'completed'},[view]);
  assert.equal(conflict.record.state,'completed');
  assert.ok(conflict.conflicts.some(issue => issue.field === 'state'));
  const stale = reconcileRecord({...base,state:'cancelled'},base,[view]);
  assert.equal(stale.record.state,'not-started');
  assert.deepEqual(stale.changes,[]);
});
