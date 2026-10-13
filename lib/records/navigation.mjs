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

/** Resolve local targets identically for navigation and migration backlinks.
 * Wiki links prefer source-relative files, then vault-relative files, trying
 * the exact name before adding .md (including dotted extensionless names).
 * Retired files may stand in for their verified pre-retirement presence so
 * deletion cannot make a surviving backlink resolve somewhere else.
 */
export async function resolveNavigationTarget(link, {sourcePath,projectsRoot,dailyPlansRoot,vaultRoot,retiredFiles = []}) {
  if ((/^[a-z][a-z\d+.-]*:/i.test(link.target) && !/^[a-z]:[\\/]/i.test(link.target)) || link.target.startsWith('//')) return null;
  const fail = (code,message) => { throw Object.assign(new Error(message),{code}); };
  let decoded;
  try { decoded = decodeURIComponent(link.target); } catch { fail('invalid-link','Invalid URL encoding'); }
  const [file,fragment] = decoded.split('#');
  const roots = [...new Set([projectsRoot,dailyPlansRoot,vaultRoot].filter(Boolean))].map(root=>{
    if (!path.isAbsolute(root)) throw new TypeError('Navigation roots must be absolute');
    return path.resolve(root);
  });
  const check = filename => {
    const root = roots.find(root=>within(root,filename));
    if (!root || path.relative(root,filename).split(path.sep).some(part=>part.startsWith('.'))) fail('unsafe-link','Target is outside allowed roots or inside hidden state');
  };
  const stat = async filename => {
    check(filename);
    try { return await safePath(filename); }
    catch (error) { if (error.code !== 'ENOENT') fail('unsafe-link',error.message); }
  };
  let filename = file ? path.resolve(path.dirname(sourcePath),file) : sourcePath;
  if (link.wiki && file) {
    const bases = [filename];
    if (vaultRoot && !path.isAbsolute(file) && !file.split(/[\\/]/).some(part=>part === '..')) {
      const vaultCandidate = path.resolve(vaultRoot,file);
      if (!bases.includes(vaultCandidate)) bases.push(vaultCandidate);
    }
    let found;
    for (const base of bases) {
      for (const candidate of [base,`${base}.md`]) {
        const stats = await stat(candidate);
        if (stats?.isFile() || (stats && candidate === base) || retiredFiles.includes(candidate)) { found = candidate; break; }
      }
      if (found) break;
    }
    filename = found ?? `${bases[0]}.md`;
  }
  await stat(filename);
  return {filename,fragment};
}

/** Inspect local wiki and Markdown navigation, including criterion evidence and attachments. */
export async function inspectNavigation(input) {
  const projectsRoot = input.projectsRoot;
  const dailyPlansRoot = input.dailyPlansRoot;
  const vaultRoot = input.vaultRoot;
  for (const root of [projectsRoot,dailyPlansRoot,vaultRoot].filter(Boolean)) {
    if (!path.isAbsolute(root ?? '')) throw new TypeError('Navigation roots must be absolute');
  }
  const records = await collectManagedRecords(path.resolve(projectsRoot));
  if (dailyPlansRoot) {
    const plans = path.resolve(dailyPlansRoot);
    await safePath(plans);
    for (const name of await readdir(plans)) {
      if (!/^\d{4}\.\d{2}\.\d{2}-daily-plan\.md$/.test(name)) continue;
      const filename = path.join(plans,name);
      if ((await safePath(filename)).isFile()) records.push({path:filename,markdown:await readFile(filename,'utf8')});
    }
  }
  const diagnostics = [];
  const targets = new Map();
  let checkedLinks = 0;
  for (const record of records) {
      const evidenceTargets = new Set((record.criteria ?? []).flatMap(criterion => navigationLinks(criterion.text).map(link => link.target)));
      for (const link of navigationLinks(record.markdown)) {
        if ((/^[a-z][a-z\d+.-]*:/i.test(link.target) && !/^[a-z]:[\\/]/i.test(link.target)) || link.target.startsWith('//')) continue;
        checkedLinks++;
        const emit = (code,message)=>diagnostics.push({code,message,source:record.path,target:link.target});
        try {
          const {filename,fragment} = await resolveNavigationTarget(link,{sourcePath:record.path,projectsRoot,dailyPlansRoot,vaultRoot});
          const file = decodeURIComponent(link.target).split('#')[0];
          const requiredFile = evidenceTargets.has(link.target) && file && !/[\\/]$/.test(file) && path.extname(file) !== '';
          const stats = await safePath(filename);
          const kind = stats.isFile() ? 'file' : stats.isDirectory() ? 'directory' : null;
          if (!kind || (kind === 'directory' && requiredFile)) {
            emit('invalid-link-target','Target is not a regular file'); continue;
          }
          if (!targets.has(filename)) targets.set(filename,{path:filename,kind,sha256:null});
          if (kind === 'directory' && fragment !== undefined) {
            emit('invalid-link-target','Heading targets require a regular file'); continue;
          }
          if (fragment) {
            if (!/\.md$/i.test(filename)) emit('unverifiable-anchor','Anchors on non-Markdown attachments are not inspected');
            else {
              const text = await readFile(filename,'utf8');
              targets.set(filename,{path:filename,kind,sha256:createHash('sha256').update(text).digest('hex')});
              if (!headings(text).has(fragment.toLowerCase())) emit('missing-heading','Heading target does not exist');
            }
          }
        } catch (error) {
          emit(error.code === 'ENOENT' ? 'missing-link-target' : error.code === 'invalid-link' ? 'invalid-link' : 'unsafe-link',error.message);
        }
      }
  }
  return {records:records.map(record=>record.path),checkedLinks,diagnostics,targets:[...targets.values()]};
}
