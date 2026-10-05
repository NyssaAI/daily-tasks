import test from 'node:test';
import assert from 'node:assert/strict';
import { parseRecord, validateRecords, checkClosure, checkLinks } from '../lib/records/records.mjs';

const id = n => `019a1234-5678-7abc-8def-${String(n).padStart(12, '0')}`;
const record = (n, type, extra = {}) => ({ id: id(n), type, path: `/project/${n}.md`, title: `Record ${n}`,
  owner: 'owner@example.test', state: type === 'blocker' ? 'open' : 'not-started',
  created_at: '2026-10-05T12:00:00Z', updated_at: '2026-10-05T12:00:00Z',
  depends_on: [], blocks: [], blocked_by: [], criteria: [], refs: [], ...extra });
const graph = () => [record(1, 'project'), record(2, 'milestone', { project_id: id(1) }),
  record(3, 'task', { project_id: id(1), milestone_id: id(2), state: 'completed' }),
  record(4, 'dod', { project_id: id(1), milestone_id: id(2), state: undefined,
    criteria: [{id: id(5), text: 'Installation verified', checked: true}] })];

test('parse scalar frontmatter, hidden identity, relations and criterion IDs', () => {
  const text = `---\ntype: dod\nowner: "owner@example.test"\ncreated_at: 2026-10-05T12:00:00Z\nupdated_at: 2026-10-05T12:00:00Z\nproject_id: ${id(1)}\nmilestone_id: ${id(2)}\n---\n<!-- id: ${id(4)} -->\n# Definition of Done\n- [x] Installation verified\n  <!-- id: ${id(5)} -->\n## Blocked by\n- [[../../blockers/access|Access approval]]\n  <!-- ref: ${id(6)} -->\n`;
  const parsed = parseRecord(text, '/project/milestone/definition-of-done.md');
  assert.equal(parsed.id, id(4));
  assert.equal(parsed.criteria[0].id, id(5));
  assert.equal(parsed.criteria[0].checked, true);
  assert.deepEqual(parsed.blocked_by, [id(6)]);
  assert.equal(parsed.refs[0].target, '../../blockers/access');
  assert.deepEqual(validateRecords([parsed]).filter(d => d.code !== 'missing-reference'), []);
});

test('invalid states, dates, metadata, duplicate IDs and unsupported YAML are surfaced', () => {
  const bad = record(1, 'task', { owner: 'agent', state: 'paused', created_at: '2026-02-30T10:00:00Z' });
  const codes = validateRecords([bad, {...bad}]).map(d => d.code);
  for (const code of ['duplicate-id', 'invalid-owner', 'invalid-state', 'invalid-time']) assert.ok(codes.includes(code), code);
  const parsed = parseRecord('---\ntype: task\nowner:\n  nested: yes\n---\n# Task');
  assert.ok(validateRecords([parsed]).some(d => d.code === 'invalid-frontmatter'));
});

test('milestone closure needs DoD, resolved tasks and no open blocker; dependencies are informational', () => {
  const records = graph();
  assert.equal(checkClosure(id(2), records).allowed, true);
  records[2].state = 'not-started';
  assert.equal(checkClosure(id(2), records).allowed, false);
  records[2].state = 'cancelled';
  assert.equal(checkClosure(id(2), records).allowed, true);
  records[2].depends_on = [id(999)];
  assert.equal(checkClosure(id(2), records).allowed, true);
  records.push(record(6, 'blocker', {blocks: [id(2)]}));
  records[1].blocked_by = [id(6)];
  assert.equal(checkClosure(id(2), records).allowed, false);
  records[4].state = 'resolved';
  assert.equal(checkClosure(id(2), records).allowed, true);
});

test('missing or invalid closure relationships cannot falsely permit closure', () => {
  const records = graph();
  records[1].blocked_by = [id(99)];
  assert.equal(checkClosure(id(2), records).allowed, false);
  records[1].blocked_by = [];
  records[3].criteria[0].checked = false;
  assert.equal(checkClosure(id(2), records).allowed, false);
  assert.equal(checkClosure(id(2), records.slice(0, 3)).allowed, false);
  assert.equal(checkClosure(id(1), records).allowed, false);
  records[1].state = 'cancelled';
  assert.equal(checkClosure(id(1), records).allowed, true);
});

test('link checks propose path repairs by identity and expose missing backlinks', () => {
  const records = [record(1, 'task', {path:'/p/a.md', blocked_by:[id(2)], refs:[{id:id(2), target:'old', relation:'blocked_by'}]}),
    record(2, 'blocker', {path:'/p/new.md'})];
  const original = structuredClone(records);
  const diagnostics = checkLinks(records);
  assert.ok(diagnostics.some(d => d.code === 'path-mismatch' && d.proposedTarget === 'new'));
  assert.ok(diagnostics.some(d => d.code === 'missing-backlink'));
  assert.deepEqual(records, original);
});

test('malformed collections diagnose rather than crash and missing index refs gate closure', () => {
  const malformed = record(1, 'project', {criteria:{bad:true},refs:'bad',blocked_by:{bad:true}});
  assert.ok(validateRecords([malformed]).length > 0);
  assert.equal(checkClosure(id(1), [malformed]).allowed, false);
  const records = graph();
  records[1].refs = [{id:id(99),target:'missing-task'}];
  assert.equal(checkClosure(id(2), records).allowed, false);
});

test('DoD identity collisions and parent mismatch cannot pass closure', () => {
  const records = graph();
  records[3].criteria[0].id = records[2].id;
  assert.equal(checkClosure(id(2), records).allowed, false);
  records[3].criteria[0].id = id(5);
  records[2].project_id = id(90);
  assert.equal(checkClosure(id(2), records).allowed, false);
});

test('project criterion projections use ref IDs without requiring another wiki link', () => {
  const parsed = parseRecord(`---\ntype: project\ntags: ["reference"]\n---\n<!-- id: ${id(1)} -->\n# Project\n- [ ] [[milestone|Milestone]] <!-- ref: ${id(2)} -->\n  - [x] Criterion displayed here <!-- ref: ${id(5)} -->\n- [ ] Manually added candidate\n`);
  assert.deepEqual(parsed.parse_errors,[]);
  assert.equal(parsed.refs.length,1);
  assert.equal(parsed.projections[1].id,id(5));
  assert.equal(parsed.projections[1].checked,true);
  assert.equal(parsed.projections[2].id,undefined);
});

test('code examples do not create spurious identities or relations', () => {
  const parsed = parseRecord(`---\ntype: project\n---\n<!-- id: ${id(1)} -->\n# Project\n\`\`\`markdown\n<!-- id: ${id(2)} -->\n- [ ] [[Example]] <!-- ref: ${id(3)} -->\n\`\`\`\n`);
  assert.deepEqual(parsed.parse_errors,[]);
  assert.equal(parsed.refs.length,0);
});
