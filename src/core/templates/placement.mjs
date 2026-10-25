import { readdir, lstat } from 'node:fs/promises';
import path from 'node:path';
import { templateFiles } from './catalog.mjs';
import { readTemplateFile } from './storage.mjs';

export async function inspectWorkspaceTemplateLayout(boundWorkspace) {
  if (!boundWorkspace) return {status:'unbound',directory:null};
  const entries = await readdir(boundWorkspace,{withFileTypes:true});
  const roles = Object.fromEntries(['projects','areas','resources','archives'].map(role => [role,[]]));
  for (const entry of entries) {
    const role = entry.name.toLowerCase().replace(/^\d+[ ._-]+/,'').replace(/^archive$/,'archives');
    if (roles[role]) roles[role].push(entry);
  }
  if (Object.values(roles).some(matches => !matches.length)) return {status:'not-para',directory:null};
  if (Object.values(roles).some(matches => matches.length !== 1)) return {status:'ambiguous',directory:null};
  for (const [entry] of Object.values(roles)) {
    const stats = await lstat(path.join(boundWorkspace,entry.name));
    if (!stats.isDirectory() || stats.isSymbolicLink()) return {status:'unsafe',directory:null};
  }
  return {status:'para',directory:path.join(boundWorkspace,roles.resources[0].name,'templates')};
}

export async function discoverWorkspaceTemplate(boundWorkspace,kind) {
  if (!boundWorkspace || !templateFiles[kind]) return null;
  const layout = await inspectWorkspaceTemplateLayout(boundWorkspace);
  if (layout.status === 'ambiguous' || layout.status === 'unsafe') return null;
  const directories = [
    ...(layout.directory ? [layout.directory] : []),
    path.join(boundWorkspace,'templates'),
  ];
  const filenames = [
    templateFiles[kind],
    ...(kind === 'planDayReview' ? ['plan-day-review.md'] : []),
  ];
  for (const directory of directories) {
    for (const name of filenames) {
      const candidate = path.join(directory,name);
      const content = await readTemplateFile(candidate);
      if (content !== null) return {path:candidate,content};
    }
  }
  return null;
}

/** Propose skill-owned template placement; never create directories, files or preferences. */
export async function templatePlacement(context,templates) {
  const boundWorkspace = context.workspaceRoot ?? context.vaultRoot;
  const layout = await inspectWorkspaceTemplateLayout(boundWorkspace);
  if (layout.status !== 'para') return {status:layout.status,templates:{}};
  const directory = layout.directory;
  const proposed = {};
  for (const [kind,row] of Object.entries(templates)) {
    if (row.transient) { proposed[kind] = {status:'one-off'}; continue; }
    if (row.sourcePath && !row.discovered) { proposed[kind] = {status:'configured',path:row.sourcePath}; continue; }
    if (context.preferenceSources[`templates.${kind}`]) { proposed[kind] = {status:'bundled-reset'}; continue; }
    const filename = path.join(directory,templateFiles[kind]);
    const existing = await readTemplateFile(filename);
    proposed[kind] = {status:existing === null ? 'create' : 'existing',path:filename,
      profileValue:'./'+path.relative(boundWorkspace,filename).split(path.sep).join('/'),
      content:row.active.content,revision:row.active.revision};
  }
  return {status:'para',directory,templates:proposed};
}
