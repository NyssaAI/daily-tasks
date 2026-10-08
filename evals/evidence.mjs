import { readFile } from 'node:fs/promises';
import path from 'node:path';
import { createHash } from 'node:crypto';

const legacyScenarioIds = ['acceptance','assignment-time','reconciliation','day-change','closure','configuration-discovery'];
export const scenarioIds = [...legacyScenarioIds,'milestone-workspace','workspace-migration'];
export const deterministicCommands = [['node','--test'],['node','scripts/assemble.mjs','check'],['node','scripts/validate.mjs']];
export async function verifyResult(result, directory, target) {
  if (!target || result.target !== target.id || result.kind !== target.kind || result.platform !== target.platform || result.configuration !== target.configuration || result.suite !== target.suite || !['pass','fail'].includes(result.status) || !/^[a-zA-Z0-9-]+$/.test(result.runId) || !Number.isFinite(Date.parse(result.completed_at)) || !/^[a-f0-9]{64}$/.test(result.candidate?.hash || '')) throw new Error('Invalid result identity or matrix coordinates');
  const evidence = async item => {
    if (!item || typeof item.output !== 'string' || !/^[a-zA-Z0-9][a-zA-Z0-9_.-]*$/.test(item.output)) throw new Error('Invalid evidence path');
    const bytes = await readFile(path.join(directory,item.output));
    if (createHash('sha256').update(bytes).digest('hex') !== item.sha256) throw new Error('Evidence changed');
  };
  if (target.kind === 'deterministic') {
    if (!Array.isArray(result.commands) || result.commands.length !== deterministicCommands.length) throw new Error('Missing deterministic commands');
    for (const [index,command] of result.commands.entries()) {
      if (JSON.stringify(command.command) !== JSON.stringify(deterministicCommands[index])) throw new Error('Wrong deterministic command');
      await evidence(command);
    }
    if (result.status === 'pass' && result.commands.some(command => command.exit !== 0)) throw new Error('False command pass');
  } else if (target.kind === 'host') {
    const requiredScenarios = target.suite === 'workflow-v2' ? legacyScenarioIds : scenarioIds;
    if (typeof result.hostVersion !== 'string' || !result.hostVersion || typeof result.model !== 'string' || !result.model) throw new Error('Host version and model receipt required');
    if (result.discovery?.isolated !== true || !Array.isArray(result.discovery.loadedSkills) || !result.discovery.loadedSkills.length) throw new Error('Isolated discovery evidence required');
    await evidence(result.discovery);
    if (!Array.isArray(result.scenarios) || result.scenarios.length !== requiredScenarios.length || new Set(result.scenarios.map(s => s.id)).size !== requiredScenarios.length) throw new Error('Incomplete scenario inventory');
    for (const scenario of result.scenarios) {
      if (!requiredScenarios.includes(scenario.id) || !['pass','fail'].includes(scenario.status)) throw new Error('Invalid scenario');
      await evidence(scenario);
    }
    if (result.status === 'pass' && result.scenarios.some(scenario => scenario.status !== 'pass')) throw new Error('False host pass');
  } else throw new Error('Provisional contract cannot supply release evidence');
  if (result.status === 'pass' && result.source_unchanged !== true) throw new Error('Candidate changed during run');
  return result;
}
export function releaseReady(targets, latest, candidateHash) {
  return targets.filter(target => target.required).every(target => {
    const result = latest.get(target.id);
    return result?.status === 'pass' && result.candidate.hash === candidateHash;
  });
}
