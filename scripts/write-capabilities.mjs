import { writeFile } from 'node:fs/promises';
import { root } from './assemble.mjs';
import path from 'node:path';

const definitions = {
  'new-id':[], 'activity-time':[], 'local-day':['timezone'], 'format-time':['time','timezone'],
  'validate-profile':['user','timezone','priorities','vaultRoot','projectsRoot'],
  'resolve-context':[], 'project-index':['vaultRoot','projectsRoot','dailyPlansRoot','timezone'],
  'planning-prepare':[], 'planning-state':['action','expectedPlanHash','expectedPreviousHash','expectedStateHash','expectedInventoryHash'],
  'invalidate-project-index':['vaultRoot'], 'planning-review':['inventory','userEmail','timezone','contextBinding','inventoryBinding'],
  'plan-selection':['inventory','taskIds','action','today','dailyPlansRoot','contextBinding','inventoryBinding'], 'maintenance-status':[],
  'parse-record':['markdown'], 'parse-checklist':['markdown'], 'inspect-records':['projectsRoot'],
  'validate-records':['records'], 'check-links':['records'], 'check-closure':['recordId','records'],
  'reconcile-record':['base','current','views'], 'reopen-ancestors':['records','changedIds'],
  'recover-operation':['operation','actual'], 'carry-forward':['rows','records','userEmail','contextBinding'],
  'plan-rollover':['today','planId','userEmail','contextBinding'],
  'log-append':['projectsRoot','entry'], 'log-query':['projectsRoot'], 'log-archive':['projectsRoot'],
};
const operations = Object.entries(definitions).map(([name,required]) => ({name,path:'bin/daily-tasks.mjs',
  purpose:`${name.replaceAll('-',' ')}; see skills/daily-tasks/references/cli.md`,
  inputSchema:{type:'object',required:[...new Set([...required,...(['planning-review','plan-selection','carry-forward','plan-rollover'].includes(name) ? ['vaultRoot','projectsRoot','dailyPlansRoot'] : [])])]},outputSchema:{type:'object'},
  sideEffects:name === 'log-append' ? 'append-log' : name === 'log-archive' ? 'archive-log' : name === 'log-query' ? 'temporary-lock' : name === 'planning-state' ? 'planning-state' : ['project-index','invalidate-project-index','planning-prepare'].includes(name) ? 'derived-cache' : 'none',
  requiredEnvironment:[],dryRun:['log-append','log-archive','log-query','project-index','invalidate-project-index','planning-prepare','planning-state'].includes(name),
  invocation:`node bin/daily-tasks.mjs ${name}${name === 'new-id' ? '' : ' --input ABSOLUTE_JSON_FILE'}` }));
await writeFile(path.join(root,'capabilities.json'),JSON.stringify({schemaVersion:1,operations},null,2)+'\n');
