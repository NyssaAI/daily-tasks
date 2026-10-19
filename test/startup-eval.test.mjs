import test from 'node:test';
import assert from 'node:assert/strict';
import { runStartupBenchmark } from '../evals/startup-benchmark.mjs';

test('startup eval benchmark enforces health-check, UTF-16LE BOM decoding, latency budget and single-pass authoring', async () => {
  const result = await runStartupBenchmark();
  assert.equal(result.status, 'pass');
  assert.ok(result.healthElapsed < 500, `Health check took too long: ${result.healthElapsed}ms`);
  assert.ok(result.prepareElapsed < 1500, `Preparation latency exceeded budget: ${result.prepareElapsed}ms`);
  assert.equal(result.tasksIndexed, 40);
  assert.ok(result.rolloverSelected > 0);
  assert.ok(result.taskSources > 0);
});
