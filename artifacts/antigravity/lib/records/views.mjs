const refComment = /<!--\s*ref:\s*([^\s>]+)\s*-->/g;

/** A following-line reference consists only of hidden ref comments. */
export function viewReferenceLine(line) {
  if (!/^\s*(?:<!--\s*ref:\s*[^\s>]+\s*-->\s*)+$/.test(line)) return null;
  return [...line.matchAll(refComment)].map(match => match[1]);
}

/** Agreeing references retain identity; conflicting references never choose a winner. */
export function associateViewReferences(row, references) {
  if (row.referenceError) return;
  const identities = new Set([...(row.id ? [row.id] : []),...references]);
  if (identities.size > 1) { row.id = null; row.referenceError = 'Conflicting reference IDs'; }
  else row.id = [...identities][0] ?? null;
}

/** Parse referenced list/table cells; escaped wiki pipes are labels, not columns. */
export function parseViewRows(markdown) {
  const rows = [];
  let fence, comment = false, pending;
  for (const line of markdown.split(/\r?\n/)) {
    const previous = pending;
    pending = undefined;
    if (comment) { if (line.includes('-->')) comment = false; continue; }
    const fenced = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
    if (fenced) { if (!fence) fence = fenced[1]; else if (fenced[1][0] === fence[0] && fenced[1].length >= fence.length) fence = undefined; continue; }
    if (fence) continue;
    if (/^\s*<!--(?!\s*(?:ref|id):)/.test(line)) { comment = !line.includes('-->'); continue; }
    const adjacent = viewReferenceLine(line);
    if (adjacent && previous) {
      associateViewReferences(previous,adjacent);
      previous.candidate = !previous.id && !previous.referenceError;
      continue;
    }
    const table = /^\s*\|/.test(line);
    if (!table && !/^\s*[-*]\s+/.test(line)) continue;
    const cells = table ? line.split(/(?<!\\)\|/).filter(Boolean) : [line.replace(/^\s*[-*]\s+/,'')];
    const statusCell = table && cells.find(cell => /^\s*\[[ xX>\-]\]\s*$/.test(cell));
    for (const cell of cells) {
      if (table && /^\s*\[[ xX>\-]\]\s*$/.test(cell)) continue;
      const mark = /^\s*\[([ xX>\-])\]\s*(.+)/.exec(cell);
      const linkOnly = table && /\[\[/.test(cell);
      if (!mark && !linkOnly) continue;
      const text = (mark?.[2] ?? cell).replaceAll('\\|','|');
      const references = [...text.matchAll(refComment)].map(match => match[1]);
      const link = /\[\[([^\]|]+)(?:\|([^\]]+))?\]\]/.exec(text);
      const title = text.replace(/<!--.*?-->/g,'').trim();
      const symbol = (mark?.[1] ?? (linkOnly && statusCell ? /\[([ xX>\-])\]/.exec(statusCell)[1] : undefined))?.toLowerCase();
      const cancelled = symbol === '-' || (symbol === ' ' && /~~.+~~.*\bCancelled\b/i.test(title));
      const row = {id:null,title,target:link?.[1],label:link?.[2] ?? link?.[1],
        checked:symbol === 'x',mark:symbol,cancelled,
        ...(cancelled ? {state:'cancelled'} : symbol === '>' ? {state:'in-progress'} : {})};
      associateViewReferences(row,references);
      row.candidate = !row.id && !row.referenceError;
      rows.push(row);
      if (!table) pending = row;
    }
  }
  return rows;
}
