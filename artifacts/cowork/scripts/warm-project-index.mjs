#!/usr/bin/env node
import { readFile } from 'node:fs/promises';
import { homedir } from 'node:os';
import path from 'node:path';
import { warmProjectIndex } from '../lib/inventory/warm.mjs';

function help(version) {
  return {
    name:'warm-project-index',
    version,
    usage:'node <installed-entry-path> --vault-root ABSOLUTE_PATH [--home-root ABSOLUTE_PATH] [--profile-path ABSOLUTE_PATH | --configuration-sources JSON] [--state-root ABSOLUTE_PATH] [--dry-run]',
    effect:'Resolves configured Daily Tasks context and invokes stale-on-demand project-index refresh. It never forces refresh and writes only disposable derived cache files.',
    scope:'vaultRoot is required and must be absolute. homeRoot defaults to the current user home; cwd never selects a vault.',
    exits:'0: one compact JSON result. 1: one JSON error on stderr.',
  };
}

function parse(argv) {
  const input = {};
  const seen = new Set();
  while (argv.length) {
    const flag = argv.shift();
    if (flag === '--dry-run') {
      if (seen.has(flag)) throw new Error(`Duplicate argument: ${flag}`);
      seen.add(flag);
      input.dryRun = true;
      continue;
    }
    const key = {'--vault-root':'vaultRoot','--home-root':'homeRoot','--profile-path':'profilePath','--configuration-sources':'configurationSources','--state-root':'stateRoot'}[flag];
    if (!key || seen.has(flag)) throw new Error(`Unknown or duplicate argument: ${flag}`);
    seen.add(flag);
    const value = argv.shift();
    if (key === 'configurationSources') {
      if (!value) throw new Error('--configuration-sources requires one JSON argument');
      input[key] = JSON.parse(value);
      continue;
    }
    if (!value || !path.isAbsolute(value)) throw new Error(`${flag} requires an absolute path`);
    input[key] = value;
  }
  if (!input.vaultRoot) throw new Error('--vault-root requires an absolute path');
  input.homeRoot ??= homedir();
  return input;
}

async function main() {
  const argv = process.argv.slice(2);
  if (argv.includes('--help')) {
    if (argv.length !== 1) throw new Error('--help cannot be combined with other arguments');
    const {version} = JSON.parse(await readFile(new URL('../package.json',import.meta.url),'utf8'));
    console.log(JSON.stringify(help(version)));
    return;
  }
  console.log(JSON.stringify(await warmProjectIndex(parse(argv))));
}

main().catch(error => {
  console.error(JSON.stringify({error:error.message,code:error.code || 'INVALID_OPERATION'}));
  process.exitCode = 1;
});
