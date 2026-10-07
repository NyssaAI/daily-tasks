import { parseViewRows, associateViewReferences, viewReferenceLine } from './views.mjs';

const relations = new Map([['depends on','depends_on'], ['required by','required_by'],
  ['blocks','blocks'], ['blocked by','blocked_by']]);
const idComment = /<!--\s*id:\s*([^\s>]+)\s*-->/g;
const refComment = /<!--\s*ref:\s*([^>]*?)\s*-->/g;

/** Recognize managed records even when a type field is mistyped; ordinary project notes stay out. */
export function recordMarkdownIsManaged(markdown, filename = '') {
  const metadata = /^\uFEFF?---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)/.exec(markdown)?.[1] ?? '';
  const conventional = ['project-index.md','milestone.md','definition-of-done.md'].includes(filename.split(/[\\/]/).at(-1).toLowerCase());
  return conventional || /^type:\s*["']?(project|milestone|task|blocker|dod)["']?\s*$/m.test(metadata) ||
    /^(project_id|milestone_id):/m.test(metadata);
}

function scalar(value) {
  if (!value || /^[\[\]{}|>&*!]/.test(value)) throw new Error('Expected a scalar value');
  if (value.startsWith('"')) {
    const parsed = JSON.parse(value);
    if (typeof parsed !== 'string') throw new Error('Expected a quoted string');
    return parsed;
  }
  if (value.startsWith("'")) {
    if (!/^'(?:[^']|'')*'$/.test(value)) throw new Error('Invalid single-quoted scalar');
    return value.slice(1, -1).replaceAll("''", "'");
  }
  if (/\s+#/.test(value)) throw new Error('Quote strings containing inline comments');
  if (value === 'null' || value === '~') return null;
  return value;
}

/** Parse the deliberately small scalar-frontmatter Markdown contract, never full YAML. */
export function parseRecord(markdown, path) {
  if (typeof markdown !== 'string') throw new TypeError('Markdown must be text');
  const lines = markdown.replace(/^\uFEFF/, '').replaceAll('\r\n', '\n').split('\n');
  const metadata = Object.create(null);
  const errors = [];
  let start = 0;
  if (lines[0] !== '---') errors.push('Missing scalar frontmatter');
  else {
    const end = lines.indexOf('---', 1);
    if (end < 0) errors.push('Unterminated frontmatter');
    else {
      start = end + 1;
      for (const line of lines.slice(1, end)) {
        if (!line.trim() || line.trimStart().startsWith('#')) continue;
        const match = /^([a-z][a-z0-9_-]*):\s*(.*?)\s*$/.exec(line);
        if (!match) { errors.push(`Unsupported frontmatter line: ${line}`); continue; }
        const [, key, value] = match;
        if (Object.hasOwn(metadata, key)) { errors.push(`Duplicate frontmatter key: ${key}`); continue; }
        try {
          if (key === 'tags' && value.startsWith('[')) {
            const tags = JSON.parse(value);
            if (!Array.isArray(tags) || tags.some(tag => typeof tag !== 'string')) throw new Error('tags must be a JSON array of strings');
            metadata[key] = tags;
          } else metadata[key] = scalar(value);
        } catch (error) { errors.push(`${key}: ${error.message}`); }
      }
    }
  }
  const record = {id: metadata.id, type:metadata.type, path, title:metadata.title,
    owner:metadata.owner, state:metadata[`${metadata.type}-state`], depends_on:[], required_by:[],
    blocks:[], blocked_by:[], criteria:[], refs:[], projections:[], parse_errors:errors};
  for (const key of ['assignee','created_at','updated_at','started_at','resolved_at','target_date','project_id','milestone_id']) {
    if (Object.hasOwn(metadata,key)) record[key] = metadata[key];
  }
  if (metadata['document-maturity']) record['document-maturity'] = metadata['document-maturity'];
  if (metadata.status || metadata.state) errors.push('Use document-maturity and the type-specific state key');
  let relation;
  let pendingCriterion;
  let pendingProjection;
  let pendingLink;
  let sawChecklist = false;
  let fence;
  let legacyIdSeen = false;
  let comment = false;
  const managedLinks = new WeakSet();
  const linkCounts = new WeakMap();
  for (const line of lines.slice(start)) {
    if (comment) { if (line.includes('-->')) comment = false; continue; }
    const fenceMatch = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
    if (fenceMatch) {
      if (!fence) fence = fenceMatch[1];
      else if (fenceMatch[1][0] === fence[0] && fenceMatch[1].length >= fence.length) fence = undefined;
      pendingCriterion = pendingLink = pendingProjection = undefined;
      continue;
    }
    if (fence) continue;
    if (/^\s*<!--(?!\s*(?:id|ref):)/.test(line)) {
      comment = !line.includes('-->');
      pendingCriterion = pendingLink = pendingProjection = undefined;
      continue;
    }
    if (/^\s*\|/.test(line)) {
      for (const row of parseViewRows(line)) {
        if (row.referenceError) errors.push(row.referenceError);
        if (row.mark !== undefined) record.projections.push({id:row.referenceError ? null : row.id ?? undefined,text:row.title,checked:row.checked,
          ...(row.state ? {state:row.state} : {})});
        if (row.target && (row.id || row.referenceError || row.mark !== undefined || relation)) {
          const reference = {id:row.referenceError ? null : row.id ?? undefined,target:row.target,label:row.label,relation};
          record.refs.push(reference);
          managedLinks.add(reference);
        }
        if (relation && row.id) record[relation].push(row.id);
      }
      pendingCriterion = pendingLink = pendingProjection = undefined;
      continue;
    }
    const heading = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
    if (heading) {
      if (heading[1] === '#' && !record.title) record.title = heading[2];
      relation = relations.get(heading[2].trim().toLowerCase());
      pendingCriterion = undefined;
      pendingProjection = undefined;
      pendingLink = undefined;
    }
    const checklist = /^\s*[-*]\s+\[([ xX>\-])\]\s+(.+)$/.exec(line);
    if (checklist) {
      sawChecklist = true;
      pendingCriterion = undefined;
      pendingProjection = undefined;
      pendingLink = undefined;
      if (record.type === 'dod' && !relation) {
        if (![' ','x','X'].includes(checklist[1])) errors.push('DoD criteria require an open or completed checkbox');
        pendingCriterion = {id:undefined, text:checklist[2].replace(/<!--.*?-->/g, '').trim(), checked:checklist[1].toLowerCase() === 'x'};
        record.criteria.push(pendingCriterion);
      } else if (record.type !== 'dod') {
        const row = parseViewRows(line)[0];
        pendingProjection = {id:undefined,text:row.title,checked:row.checked,
          ...(row.state ? {state:row.state} : {})};
        record.projections.push(pendingProjection);
      }
    }
    for (const match of line.matchAll(idComment)) {
      if (pendingCriterion) {
        if (pendingCriterion.id) errors.push('Multiple IDs for a DoD criterion');
        else pendingCriterion.id = match[1];
      } else if (!legacyIdSeen && !sawChecklist) {
        legacyIdSeen = true;
        if (record.id && record.id !== match[1]) errors.push('Frontmatter and legacy record identity disagree');
        else record.id = match[1];
      } else errors.push('Unassociated or duplicate record ID');
    }
    const links = [...line.matchAll(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g)];
    if (links.length) {
      if (!checklist) pendingProjection = undefined;
      pendingCriterion = undefined;
      pendingLink = {id:undefined, target:links[0][1], label:links[0][2] || links[0][1], relation};
      record.refs.push(pendingLink);
      linkCounts.set(pendingLink,links.length);
      if (relation || checklist) managedLinks.add(pendingLink);
    }
    const references = [...line.matchAll(refComment)].map(match => match[1]);
    const adjacent = viewReferenceLine(line);
    if (!checklist && !links.length && !adjacent) pendingLink = pendingProjection = undefined;
    if (references.length) {
      if ((checklist || links.length || adjacent) && (pendingLink || pendingProjection)) {
        if (pendingLink) managedLinks.add(pendingLink);
        const previousLinkId = pendingLink?.id;
        for (const row of [pendingLink,pendingProjection].filter(Boolean)) {
          associateViewReferences(row,references);
          if (row.referenceError) errors.push(row.referenceError);
        }
        if (relation && previousLinkId && pendingLink?.referenceError &&
            !record.refs.some(ref => ref.relation === relation && ref.id === previousLinkId)) {
          record[relation] = record[relation].filter(id => id !== previousLinkId);
        }
        if (relation && pendingLink?.id && !record[relation].includes(pendingLink.id)) record[relation].push(pendingLink.id);
        if (relation && !pendingLink) errors.push('Relationship requires a wiki link as well as a reference ID');
      } else errors.push('Unassociated reference ID');
      if (adjacent && !checklist && !links.length) pendingLink = pendingProjection = undefined;
    }
    if (!line.trim() || (!checklist && !links.length && !/<!--\s*(id|ref):/.test(line))) {
      pendingCriterion = undefined;
      pendingLink = undefined;
      pendingProjection = undefined;
    }
  }
  // Context/navigation links have no task identity. Classify after adjacent ref comments
  // have been associated, so malformed managed links still reach strict validation.
  record.refs = record.refs.filter(reference => managedLinks.has(reference));
  if (record.refs.some(reference => linkCounts.get(reference) > 1)) errors.push('Use one referenced wiki link per line');
  return record;
}
