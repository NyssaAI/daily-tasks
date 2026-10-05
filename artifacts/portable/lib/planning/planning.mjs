import { isUuid7 } from '../identity/identity.mjs';

// Pure selection support: it does not choose work, assign dates, or write files.
export function carryForward(previousRows, records, userEmail) {
  const byId = new Map();
  const duplicateIds = new Set();
  for (const record of records) {
    if (byId.has(record.id)) duplicateIds.add(record.id);
    byId.set(record.id, record);
  }
  const seen = new Set();
  const result = { own: [], delegated: [], unresolved: [] };
  for (const row of previousRows) {
    if (!isUuid7(row.id)) { result.unresolved.push({ ...row, reason: 'missing-identity' }); continue; }
    if (seen.has(row.id) || row.selected === false) continue;
    seen.add(row.id);
    const record = byId.get(row.id);
    if (duplicateIds.has(row.id) || !record) {
      result.unresolved.push({ ...row, reason: duplicateIds.has(row.id) ? 'duplicate-identity' : 'missing-record' }); continue;
    }
    if (['completed', 'cancelled'].includes(record.state)) continue;
    const effectiveAssignee = record.assignee || record.owner;
    if (effectiveAssignee === userEmail) result.own.push({ ...row, selected: true });
    else if (record.owner === userEmail) result.delegated.push({ ...row, selected: true });
    else result.unresolved.push({ ...row, reason: 'outside-user-responsibility' });
  }
  return result;
}

export function parseChecklist(markdown) {
  const rows = [];
  for (const line of markdown.split(/\r?\n/)) {
    const match = /^\s*- \[([ xX])\]\s+(.+)$/.exec(line);
    if (!match) continue;
    const ref = /<!--\s*ref:\s*([\w-]+)\s*-->/.exec(match[2]);
    const label = match[2].replace(/<!--.*?-->/g, '').trim();
    rows.push({ id: ref?.[1] || null, checked: match[1].toLowerCase() === 'x', title: label,
      cancelled: /~~.+~~\s*[—-]\s*Cancelled/.test(label), candidate: !ref });
  }
  return rows;
}
