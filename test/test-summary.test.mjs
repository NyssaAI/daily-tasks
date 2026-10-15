import test from 'node:test';
import assert from 'node:assert/strict';
import { parseTapSummary, resultSummary } from '../scripts/run-tests.mjs';

test('parseTapSummary reads the final Node TAP totals', () => {
  const output = [
    'TAP version 13',
    '# tests 4',
    '# pass 3',
    '# fail 1',
    '# cancelled 0',
    '# skipped 0',
    '# todo 0',
    '# duration_ms 25.4',
  ].join('\n');
  assert.deepEqual(parseTapSummary(output), {
    tests: 4,
    pass: 3,
    fail: 1,
    cancelled: 0,
    skipped: 0,
    todo: 0,
    duration_ms: 25.4,
  });
});

test('resultSummary records failed runs and retains complete TAP output', () => {
  const report = resultSummary({
    date: '2026.10.15',
    timestamp: '2026-10-15T15:00:00.000Z',
    nodeVersion: 'v22.0.0',
    exitCode: 1,
    error: '',
    output: 'TAP version 13\nnot ok 1 - sample failure\n',
    summary: { tests: 1, pass: 0, fail: 1, cancelled: 0, skipped: 0, todo: 0, duration_ms: 3 },
  });
  assert.match(report, /# Test result summary — 2026\.10\.15/);
  assert.match(report, /\*\*Status:\*\* Failed/);
  assert.match(report, /\*\*Failed:\*\* 1/);
  assert.match(report, /not ok 1 - sample failure/);
});
