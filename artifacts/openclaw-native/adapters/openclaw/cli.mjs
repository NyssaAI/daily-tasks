import { spawn } from 'node:child_process';
import { homedir } from 'node:os';
import path from 'node:path';
import { buildPrewarmAutomation } from './automation.mjs';
import { resolveContext } from '../../lib/profile/context.mjs';

function runOpenClaw(entry,args) {
  return new Promise((resolve,reject) => {
    const child = spawn(process.execPath,[entry,...args],{stdio:['ignore','pipe','pipe']});
    let stdout = '', stderr = '';
    child.stdout.setEncoding('utf8').on('data',chunk => { stdout += chunk; });
    child.stderr.setEncoding('utf8').on('data',chunk => { stderr += chunk; });
    child.on('error',reject);
    child.on('close',code => {
      if (code !== 0) return reject(new Error(stderr.trim() || `OpenClaw automation registration exited ${code}`));
      try { resolve(JSON.parse(stdout)); }
      catch { reject(new Error('OpenClaw automation registration returned invalid JSON')); }
    });
  });
}

export function registerDailyTasksCli({program,pluginRoot,gatewayConfig = {},openclawEntry = process.argv[1],run = runOpenClaw}) {
  if (!path.isAbsolute(pluginRoot ?? '')) throw new Error('Stable OpenClaw plugin root is unavailable');
  const warmCommandPath = path.join(pluginRoot,'bin/warm-project-index.mjs');
  const gatewayUrl = gatewayConfig.mode === 'remote' ? gatewayConfig.remote?.url : undefined;
  const gatewayPort = gatewayUrl === undefined && Number.isInteger(gatewayConfig.port) ? gatewayConfig.port : undefined;
  const root = program.command('daily-tasks').description('Manage Daily Tasks OpenClaw integrations');
  root.command('setup-prewarm')
    .description('Create or reconcile the optional project-index prewarm automation')
    .requiredOption('--vault-root <path>','Absolute configured vault root')
    .option('--home-root <path>','Absolute user home used for personal preferences',homedir())
    .option('--profile-path <path>','Absolute accepted legacy/custom profile path')
    .option('--configuration-sources <json>','Resolved user/project source descriptor as one JSON argument')
    .option('--state-root <path>','Absolute established operation state root')
    .option('--every <duration>','OpenClaw interval', '1h')
    .option('--disabled','Create or explicitly reconcile the job disabled',false)
    .option('--dry-run','Print the declaration without changing automations',false)
    .action(async options => {
      for (const key of ['vaultRoot','homeRoot','profilePath','stateRoot']) {
        if (options[key] !== undefined && !path.isAbsolute(options[key])) throw new Error(`--${key.replace(/[A-Z]/g,m => '-'+m.toLowerCase())} requires an absolute path`);
      }
      const selectors = {
        vaultRoot:options.vaultRoot,homeRoot:options.homeRoot,profilePath:options.profilePath,stateRoot:options.stateRoot,
        configurationSources:options.configurationSources === undefined ? undefined : JSON.parse(options.configurationSources),
      };
      const context = await resolveContext(selectors);
      if (!context.configured || !context.vaultRoot || !context.projectsRoot || !context.dailyPlansRoot) throw new Error('Configured vault context required for project-index prewarm');
      const boundSelectors = selectors.configurationSources !== undefined || selectors.stateRoot !== undefined
        ? {...selectors,configurationSources:selectors.profilePath === undefined ? context.configurationSources : undefined,stateRoot:context.stateRoot}
        : selectors;
      const declaration = buildPrewarmAutomation({
        ...boundSelectors,every:options.every,disabled:options.disabled,
        nodePath:process.execPath,
        warmCommandPath,
        gatewayUrl,
        gatewayPort,
      });
      if (options.dryRun) {
        console.log(JSON.stringify({status:'preview',...declaration}));
        return;
      }
      if (!path.isAbsolute(openclawEntry ?? '')) throw new Error('OpenClaw CLI entry path is unavailable');
      const result = await run(openclawEntry,declaration.args);
      console.log(JSON.stringify({status:'reconciled',declarationKey:declaration.declarationKey,every:declaration.every,usesAgent:false,automation:result}));
    });
}
