import test from 'node:test';
import assert from 'node:assert/strict';
import { activityTime, localDay, displayTime } from '../lib/time/time.mjs';

test('reported activity and recording time remain separate; vague time defaults', () => {
  const now = '2026-10-05T18:00:00Z';
  assert.deepEqual(activityTime('2026-10-05T15:00:00Z', now), {
    activity_at: '2026-10-05T15:00:00.000Z', recorded_at: '2026-10-05T18:00:00.000Z', time_defaulted: false,
  });
  assert.equal(activityTime('earlier today', now).time_defaulted, true);
  assert.equal(activityTime(undefined, now).activity_at, '2026-10-05T18:00:00.000Z');
});

test('invalid precise dates and implicit local timestamps fail instead of defaulting', () => {
  for (const value of ['2026-02-30T10:00:00Z', '2026-10-05T10:00:00', '2026-10-05T10:00:00-05:00', '2026-13-01', 23]) {
    assert.throws(() => activityTime(value, '2026-10-05T18:00:00Z'));
  }
});

test('local day and display use explicit zone across midnight and DST', () => {
  assert.equal(localDay('2026-10-05T02:00:00Z', 'America/Chicago'), '2026.10.04');
  assert.match(displayTime('2026-07-01T12:00:00Z', 'America/Chicago'), /CDT.*America\/Chicago/);
  assert.match(displayTime('2026-01-01T12:00:00Z', 'America/Chicago'), /CST.*America\/Chicago/);
  assert.throws(() => localDay('2026-10-05T02:00:00Z', 'bad-zone'));
});
