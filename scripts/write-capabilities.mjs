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
  'maintenance-inspect':[], 'operation-verify':['operationPath'], 'operation-complete':['operationPath'],
  'rollover-complete':['operationPath'], 'migration-retirement':['operationPath'], 'migration-complete':['operationPath'],
  'inspect-navigation':['projectsRoot'], 'next-record-number':['projectsRoot','type','parentId'],
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
  sideEffects:name === 'log-append' ? 'append-log' : name === 'log-archive' ? 'archive-log' : name === 'log-query' ? 'temporary-lock' : name === 'planning-state' ? 'planning-state' : name === 'maintenance-inspect' ? 'inspection-state' : ['operation-complete','rollover-complete','migration-complete'].includes(name) ? 'verified-state' : ['project-index','invalidate-project-index','planning-prepare'].includes(name) ? 'derived-cache' : 'none',
  requiredEnvironment:[],dryRun:['log-append','log-archive','log-query','project-index','invalidate-project-index','planning-prepare','planning-state','maintenance-inspect','operation-complete','rollover-complete','migration-complete'].includes(name),
  invocation:`node bin/daily-tasks.mjs ${name}${name === 'new-id' ? '' : ' --input ABSOLUTE_JSON_FILE'}` }));
operations.splice(operations.findIndex(operation => operation.name === 'project-index') + 1,0,
  {
    name:'template-prepare',
    path:'bin/daily-tasks.mjs',
    purpose:'Resolve retained templates, compare available revisions and determine relevant offers',
    inputSchema:{type:'object',required:['kinds']},
    outputSchema:{type:'object'},
    sideEffects:'none',
    requiredEnvironment:[],
    dryRun:false,
    invocation:'node bin/daily-tasks.mjs template-prepare --input ABSOLUTE_JSON_FILE',
  },
  {
    name:'template-state',
    path:'bin/daily-tasks.mjs',
    purpose:'Retain template snapshots and explicit choices with recoverable project logging',
    inputSchema:{type:'object',required:['kinds','action','expectedToken']},
    outputSchema:{type:'object'},
    sideEffects:'template-preferences-and-log',
    requiredEnvironment:[],
    dryRun:true,
    invocation:'node bin/daily-tasks.mjs template-state --input ABSOLUTE_JSON_FILE',
  },
  {
    name:'warm-project-index',
    path:'bin/warm-project-index.mjs',
    purpose:'Resolve configured context and invoke stale-on-demand project-index prewarming',
    inputSchema:{type:'object',required:['vaultRoot'],properties:{
      vaultRoot:{type:'string'},homeRoot:{type:'string'},profilePath:{type:'string'},dryRun:{type:'boolean'},
    }},
    outputSchema:{type:'object'},
    sideEffects:'derived-cache',
    requiredEnvironment:[],
    dryRun:true,
    invocation:'node bin/warm-project-index.mjs --vault-root ABSOLUTE_PATH [--home-root ABSOLUTE_PATH] [--profile-path ABSOLUTE_PATH] [--dry-run]',
  },
);
await writeFile(path.join(root,'capabilities.json'),JSON.stringify({schemaVersion:1,operations},null,2)+'\n');
