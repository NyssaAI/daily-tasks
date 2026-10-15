import { writeFile } from 'node:fs/promises';
import { root } from './assemble.mjs';
import path from 'node:path';
import { profileInputSchema } from '#core/profile/schema.mjs';

const sourceSelection = {type:'object',required:['profilePath'],additionalProperties:false,properties:{
  profilePath:{type:['string','null'],description:'Accepted absolute profile path, or null for deliberate absence.'},
}};

const definitions = {
  'new-id':[], 'activity-time':[], 'local-day':['timezone'], 'format-time':['time','timezone'],
  'validate-profile':[],
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
  inputSchema:name === 'validate-profile' ? profileInputSchema : {type:'object',required:[...new Set([...required,...(['planning-review','plan-selection','carry-forward','plan-rollover'].includes(name) ? ['vaultRoot','projectsRoot','dailyPlansRoot'] : [])])],
    ...(name === 'planning-state' ? {allOf:[{
      if:{properties:{action:{const:'save-review'}},required:['action']},
      then:{required:['expectedReviewHash','reviewMarkdown'],properties:{reviewMarkdown:{type:'string',minLength:1}}},
    }]} : {}),
  },outputSchema:{type:'object'},
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
    inputSchema:{type:'object',required:['vaultRoot'],not:{required:['profilePath','configurationSources']},properties:{
      vaultRoot:{type:'string'},homeRoot:{type:'string'},profilePath:{type:'string'},stateRoot:{type:'string'},dryRun:{type:'boolean'},
      configurationSources:{type:'object',required:['schemaVersion','user','project'],additionalProperties:false,
        description:'Durable source selections serialized as one JSON argv value; paths and bound scopes are validated by the resolver.',
        properties:{schemaVersion:{const:1},user:sourceSelection,project:sourceSelection}},
    }},
    outputSchema:{type:'object'},
    sideEffects:'derived-cache',
    requiredEnvironment:[],
    dryRun:true,
    invocation:'node bin/warm-project-index.mjs --vault-root ABSOLUTE_PATH [--home-root ABSOLUTE_PATH] [--profile-path ABSOLUTE_PATH | --configuration-sources JSON] [--state-root ABSOLUTE_PATH] [--dry-run]',
  },
);
await writeFile(path.join(root,'capabilities.json'),JSON.stringify({schemaVersion:1,operations},null,2)+'\n');
