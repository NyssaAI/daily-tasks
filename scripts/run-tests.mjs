import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

export function parseTapSummary(output) {
  const summary = {};
  for (const key of ['tests', 'pass', 'fail', 'cancelled', 'skipped', 'todo', 'duration_ms']) {
    const matches = [...output.matchAll(new RegExp(`^# ${key} (\\d+(?:\\.\\d+)?)$`, 'gm'))];
    const value = matches.at(-1)?.[1];
    if (value !== undefined) summary[key] = Number(value);
  }
  return summary;
}

export function resultSummary({ date, timestamp, nodeVersion, exitCode, error, output, summary }) {
  const status = exitCode === 0 && !error ? 'Passed' : 'Failed';
  const lines = [
    `# Test result summary — ${date}`,
    '',
    `- **Status:** ${status}`,
    `- **Run at:** ${timestamp}`,
    `- **Node.js:** ${nodeVersion}`,
    '- **Command:** `node --test --test-reporter=tap`',
    `- **Tests:** ${summary.tests ?? 'unavailable'}`,
    `- **Passed:** ${summary.pass ?? 'unavailable'}`,
    `- **Failed:** ${summary.fail ?? 'unavailable'}`,
    `- **Cancelled:** ${summary.cancelled ?? 'unavailable'}`,
    `- **Skipped:** ${summary.skipped ?? 'unavailable'}`,
    `- **Todo:** ${summary.todo ?? 'unavailable'}`,
    `- **Duration:** ${summary.duration_ms === undefined ? 'unavailable' : `${summary.duration_ms} ms`}`,
    `- **Exit code:** ${exitCode ?? 'not available'}`,
  ];
  if (error) lines.push(`- **Runner error:** ${error}`);
  const fence = '`'.repeat(Math.max(3, ...[...output.matchAll(/`+/g)].map(match => match[0].length + 1)));
  lines.push('', '<details>', '<summary>Full TAP output</summary>', '', `${fence}text`, output.trimEnd(), fence, '', '</details>', '');
  return lines.join('\n');
}

function dateStamp(date) {
  return [date.getFullYear(), String(date.getMonth() + 1).padStart(2, '0'), String(date.getDate()).padStart(2, '0')].join('.');
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) {
  const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
  const result = spawnSync(process.execPath, ['--test', '--test-reporter=tap'], {
    cwd: root,
    encoding: 'utf8',
    maxBuffer: 32 * 1024 * 1024,
  });
  const output = `${result.stdout || ''}${result.stderr ? `\n${result.stderr}` : ''}`;
  const error = result.error?.message || '';
  const completedAt = new Date();
  const date = dateStamp(completedAt);
  const summary = parseTapSummary(output);
  const report = path.join(root, 'test', 'results', `${date}-test-result-summary.md`);
  await mkdir(path.dirname(report), { recursive: true });
  await writeFile(report, resultSummary({
    date,
    timestamp: completedAt.toISOString(),
    nodeVersion: process.version,
    exitCode: result.status,
    error,
    output,
    summary,
  }));
  process.stdout.write(output);
  process.stdout.write(`\nTest result summary saved to ${path.relative(root, report)}\n`);
  if (result.status !== 0 || error) process.exitCode = result.status ?? 1;
}
