const relations = new Map([['depends on','depends_on'], ['required by','required_by'],
  ['blocks','blocks'], ['blocked by','blocked_by']]);
const idComment = /<!--\s*id:\s*([^\s>]+)\s*-->/g;
const refComment = /<!--\s*ref:\s*([^\s>]+)\s*-->/g;

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
  const record = {id: undefined, type:metadata.type, path, title:metadata.title,
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
  for (const line of lines.slice(start)) {
    const fenceMatch = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
    if (fenceMatch) {
      if (!fence) fence = fenceMatch[1];
      else if (fenceMatch[1][0] === fence[0] && fenceMatch[1].length >= fence.length) fence = undefined;
      pendingCriterion = pendingLink = pendingProjection = undefined;
      continue;
    }
    if (fence) continue;
    const heading = /^(#{1,6})\s+(.+?)\s*#*\s*$/.exec(line);
    if (heading) {
      if (heading[1] === '#' && !record.title) record.title = heading[2];
      relation = relations.get(heading[2].trim().toLowerCase());
      pendingCriterion = undefined;
      pendingProjection = undefined;
      pendingLink = undefined;
    }
    const checklist = /^\s*[-*]\s+\[([ xX])\]\s+(.+)$/.exec(line);
    if (checklist) {
      sawChecklist = true;
      pendingCriterion = undefined;
      pendingProjection = undefined;
      pendingLink = undefined;
      if (record.type === 'dod' && !relation) {
        pendingCriterion = {id:undefined, text:checklist[2].replace(/<!--.*?-->/g, '').trim(), checked:checklist[1] !== ' '};
        record.criteria.push(pendingCriterion);
      } else if (record.type !== 'dod') {
        pendingProjection = {id:undefined,text:checklist[2].replace(/<!--.*?-->/g,'').trim(),checked:checklist[1] !== ' '};
        record.projections.push(pendingProjection);
      }
    }
    for (const match of line.matchAll(idComment)) {
      if (pendingCriterion) {
        if (pendingCriterion.id) errors.push('Multiple IDs for a DoD criterion');
        else pendingCriterion.id = match[1];
      } else if (!record.id && !sawChecklist) record.id = match[1];
      else errors.push('Unassociated or duplicate record ID');
    }
    const links = [...line.matchAll(/\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/g)];
    if (links.length > 1) errors.push('Use one referenced wiki link per line');
    if (links.length) {
      pendingCriterion = undefined;
      pendingLink = {id:undefined, target:links[0][1], label:links[0][2] || links[0][1], relation};
      record.refs.push(pendingLink);
    }
    for (const match of line.matchAll(refComment)) {
      if (pendingLink && !pendingLink.id) {
        pendingLink.id = match[1];
        if (relation) record[relation].push(match[1]);
        if (pendingProjection) pendingProjection.id = match[1];
      } else if (pendingProjection && !pendingProjection.id) {
        pendingProjection.id = match[1];
        if (relation) errors.push('Relationship requires a wiki link as well as a reference ID');
      } else {
        errors.push('Unassociated or duplicate reference ID');
      }
    }
    if (line.trim() && !checklist && !links.length && !/<!--\s*(id|ref):/.test(line)) {
      pendingCriterion = undefined;
      pendingLink = undefined;
      pendingProjection = undefined;
    }
  }
  return record;
}
