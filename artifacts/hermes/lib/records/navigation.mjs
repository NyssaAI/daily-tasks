import { lstat, readdir, readFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';
import { parseRecord, recordMarkdownIsManaged, recordDirectoryIsHoldingArea } from './parse.mjs';

async function safePath(filename) {
  const absolute = path.resolve(filename);
  let current = path.parse(absolute).root;
  for (const part of absolute.slice(current.length).split(path.sep).filter(Boolean)) {
    current = path.join(current,part);
    if ((await lstat(current)).isSymbolicLink()) throw new Error(`Symbolic link excluded: ${current}`);
  }
  return lstat(absolute);
}

/** Collect actual managed Markdown without reading hidden state or holding areas. */
export async function collectManagedRecords(projectsRoot) {
  if (!path.isAbsolute(projectsRoot ?? '')) throw new TypeError('projectsRoot must be absolute');
  if (!(await safePath(projectsRoot)).isDirectory()) throw new TypeError('projectsRoot must be a directory');
  const records = [];
  async function visit(directory) {
    for (const entry of (await readdir(directory,{withFileTypes:true})).sort((a,b)=>a.name.localeCompare(b.name))) {
      if (entry.name.startsWith('.')) continue;
      const filename = path.join(directory,entry.name);
      const stats = await safePath(filename);
      if (stats.isDirectory()) {
        if (!recordDirectoryIsHoldingArea(path.relative(projectsRoot,filename))) await visit(filename);
      } else if (stats.isFile() && /\.md$/i.test(filename)) {
        const markdown = await readFile(filename,'utf8');
        if (recordMarkdownIsManaged(markdown,filename)) records.push({...parseRecord(markdown,filename),markdown});
      }
    }
  }
  await visit(projectsRoot);
  return records;
}

function visibleLines(markdown) {
  let fence;
  return markdown.replace(/<!--[\s\S]*?-->/g,'').split(/\r?\n/).filter(line=>{
    const match = /^\s{0,3}(`{3,}|~{3,})/.exec(line);
    if (match) {
      if (!fence) fence = match[1];
      else if (match[1][0] === fence[0] && match[1].length >= fence.length) fence = undefined;
      return false;
    }
    return !fence;
  });
}
function headings(markdown) {
  const anchors = new Set();
  const counts = new Map();
  for (const line of visibleLines(markdown)) {
    const title = /^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$/.exec(line)?.[1];
    if (!title) continue;
    anchors.add(title.toLowerCase());
    const slug = title.toLowerCase().replace(/<[^>]*>/g,'').replace(/[^\p{L}\p{N}_\-\s]/gu,'').replace(/\s/g,'-');
    const count = counts.get(slug) ?? 0;
    anchors.add(slug + (count ? `-${count}` : ''));
    counts.set(slug,count+1);
  }
  return anchors;
}
function within(root,filename) {
  const relative = path.relative(root,filename);
  return relative !== '..' && !relative.startsWith(`..${path.sep}`) && !path.isAbsolute(relative);
}

function markdownDestination(text) {
  text = text.trimStart();
  if (text.startsWith('<')) return /^<([^>\r\n]+)>/.exec(text)?.[1];
  let target = '', depth = 0;
  for (let index = 0; index < text.length; index++) {
    const character = text[index];
    if (/\s/.test(character)) break;
    if (character === '\\' && /[()<>]/.test(text[index + 1] ?? '')) { target += text[++index]; continue; }
    if (character === '(') depth++;
    if (character === ')') { if (!depth) break; depth--; }
    target += character;
  }
  return target || undefined;
}

/** Visible local-link syntax shared by navigation and retirement checks. */
export function navigationLinks(markdown) {
  const links = [];
  for (const line of visibleLines(markdown)) {
    for (const match of line.matchAll(/!?\[\[([^\]|]+)(?:\|[^\]]*)?\]\]/g)) links.push({target:match[1].replace(/\\$/,''),wiki:true});
    for (const match of line.matchAll(/!?\[[^\]]*\]\(\s*/g)) {
      const target = markdownDestination(line.slice(match.index + match[0].length));
      if (target) links.push({target,wiki:false});
    }
    const definition = /^\s{0,3}\[[^\]]+\]:\s*(.*)$/.exec(line);
    const target = definition && markdownDestination(definition[1]);
    if (target) links.push({target,wiki:false});
  }
  return links;
}

/** Inspect local wiki and Markdown navigation, including criterion evidence and attachments. */
export async function inspectNavigation(input) {
  const roots = [input.projectsRoot,...(input.dailyPlansRoot ? [input.dailyPlansRoot] : [])].map(root=>{
    if (!path.isAbsolute(root ?? '')) throw new TypeError('Navigation roots must be absolute');
    return path.resolve(root);
  });
  const records = await collectManagedRecords(roots[0]);
  if (roots[1]) {
    await safePath(roots[1]);
    for (const name of await readdir(roots[1])) {
      if (!/^\d{4}\.\d{2}\.\d{2}-daily-plan\.md$/.test(name)) continue;
      const filename = path.join(roots[1],name);
      if ((await safePath(filename)).isFile()) records.push({path:filename,markdown:await readFile(filename,'utf8')});
    }
  }
  const diagnostics = [];
  const targets = new Map();
  let checkedLinks = 0;
  for (const record of records) {
      for (const link of navigationLinks(record.markdown)) {
        if ((/^[a-z][a-z\d+.-]*:/i.test(link.target) && !/^[a-z]:[\\/]/i.test(link.target)) || link.target.startsWith('//')) continue;
        checkedLinks++;
        const emit = (code,message)=>diagnostics.push({code,message,source:record.path,target:link.target});
        let decoded;
        try { decoded = decodeURIComponent(link.target); } catch { emit('invalid-link','Invalid URL encoding'); continue; }
        const [file,fragment] = decoded.split('#');
        let filename = file ? path.resolve(path.dirname(record.path),file) : record.path;
        if (link.wiki && file && !path.extname(file)) filename += '.md';
        const root = roots.find(root=>within(root,filename));
        if (!root || path.relative(root,filename).split(path.sep).some(part=>part.startsWith('.'))) {
          emit('unsafe-link','Target is outside allowed roots or inside hidden state'); continue;
        }
        try {
          const stats = await safePath(filename);
          if (!stats.isFile()) { emit('invalid-link-target','Target is not a regular file'); continue; }
          if (!targets.has(filename)) targets.set(filename,{path:filename,sha256:null});
          if (fragment) {
            if (!/\.md$/i.test(filename)) emit('unverifiable-anchor','Anchors on non-Markdown attachments are not inspected');
            else {
              const text = await readFile(filename,'utf8');
              targets.set(filename,{path:filename,sha256:createHash('sha256').update(text).digest('hex')});
              if (!headings(text).has(fragment.toLowerCase())) emit('missing-heading','Heading target does not exist');
            }
          }
        } catch (error) {
          emit(error.code === 'ENOENT' ? 'missing-link-target' : 'unsafe-link',error.message);
        }
      }
  }
  return {records:records.map(record=>record.path),checkedLinks,diagnostics,targets:[...targets.values()]};
}
