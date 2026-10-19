#!/usr/bin/env node
import { mkdir, mkdtemp, readFile, writeFile, rm, realpath } from 'node:fs/promises';
import path from 'node:path';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import { uuid7 } from '#core/identity/identity.mjs';
import { planningScreen } from '../test/fixtures/planning-screen.mjs';

const execute = promisify(execFile);
const LATENCY_BUDGET_MS = 1500;

function generateTaskDoc({ id, title, projectId, milestoneId, state = 'not-started', now }) {
  return `---
id: ${id}
type: task
title: "${title}"
owner: owner@example.test
task-state: ${state}
created_at: ${now}
updated_at: ${now}
project_id: ${projectId}
milestone_id: ${milestoneId}
---
# ${title}

## Definition of Done
- [ ] Implement core functionality
  <!-- id: ${uuid7()} -->
- [ ] Add unit verification
  <!-- id: ${uuid7()} -->
`;
}

async function createBenchmarkVault(root, now) {
  const vaultRoot = path.join(root, 'vault');
  const settingsDir = path.join(vaultRoot, '.nyssa-ai', 'daily-tasks');
  const projectsDir = path.join(vaultRoot, '1-projects');
  const dailyPlansDir = path.join(vaultRoot, '2-areas', 'daily-plans');

  await mkdir(settingsDir, { recursive: true });
  await mkdir(projectsDir, { recursive: true });
  await mkdir(dailyPlansDir, { recursive: true });

  await writeFile(
    path.join(settingsDir, 'profile.json'),
    JSON.stringify({
      schema_version: 2,
      user: { name: 'Owner', email: 'owner@example.test' },
      timezone: 'America/Chicago',
      priorities: [],
      vaultRoot: '.',
      projectsRoot: './1-projects',
      dailyPlansRelative: '2-areas/daily-plans',
    }, null, 2)
  );

  const taskRegistry = [];
  const projects = ['alpha', 'beta', 'gamma', 'delta'];

  for (let pIdx = 0; pIdx < projects.length; pIdx++) {
    const pName = projects[pIdx];
    const projectId = uuid7();
    const projDir = path.join(projectsDir, pName);
    await mkdir(projDir, { recursive: true });

    const milestones = ['m1', 'm2'];
    const milestoneRefs = [];

    for (let mIdx = 0; mIdx < milestones.length; mIdx++) {
      const mName = milestones[mIdx];
      const milestoneId = uuid7();
      const msDir = path.join(projDir, mName);
      await mkdir(msDir, { recursive: true });

      const taskRefs = [];
      for (let tIdx = 1; tIdx <= 5; tIdx++) {
        const taskId = uuid7();
        const taskTitle = `Task ${pName}-${mName}-${tIdx}`;
        // Set some tasks to in-progress
        const state = (pIdx === 0 && mIdx === 0 && tIdx <= 2) ? 'in-progress' : 'not-started';
        const taskFile = path.join(msDir, `t${tIdx}.md`);
        await writeFile(taskFile, generateTaskDoc({ id: taskId, title: taskTitle, projectId, milestoneId, state, now }));
        taskRefs.push(`- [ ] [[t${tIdx}|${taskTitle}]] <!-- ref: ${taskId} -->`);
        taskRegistry.push({ id: taskId, title: taskTitle, path: taskFile, relativeLink: `../1-projects/${pName}/${mName}/t${tIdx}`, state });
      }

      await writeFile(
        path.join(msDir, `${mName}.md`),
        `---
id: ${milestoneId}
type: milestone
title: "Milestone ${pName}-${mName}"
owner: owner@example.test
milestone-state: not-started
created_at: ${now}
updated_at: ${now}
project_id: ${projectId}
---
# Milestone ${pName}-${mName}

## Definition of Done
- [ ] Milestone criteria met
  <!-- id: ${uuid7()} -->

## Tasks
${taskRefs.join('\n')}
`
      );
      milestoneRefs.push(`- [ ] [[${mName}/${mName}|Milestone ${mName}]] <!-- ref: ${milestoneId} -->`);
    }

    await writeFile(
      path.join(projDir, 'project-index.md'),
      `---
id: ${projectId}
type: project
title: "Project ${pName}"
owner: owner@example.test
project-state: not-started
created_at: ${now}
updated_at: ${now}
---
# Project ${pName}

${milestoneRefs.join('\n')}
`
    );
  }

  // Write yesterday's daily plan with 4 tasks selected: 2 done, 2 carried
  const yesterdayDate = '2026.10.18';
  const yesterdayPlanId = uuid7();
  const carriedTask1 = taskRegistry[0];
  const carriedTask2 = taskRegistry[1];
  const doneTask = taskRegistry[2];

  await writeFile(
    path.join(dailyPlansDir, `${yesterdayDate}-daily-plan.md`),
    `---
id: ${yesterdayPlanId}
type: daily-plan
created_at: 2026-10-18T12:00:00.000Z
---
# Yesterday's Plan

- [ ] [[${carriedTask1.relativeLink}|${carriedTask1.title}]] <!-- ref: ${carriedTask1.id} -->
- [ ] [[${carriedTask2.relativeLink}|${carriedTask2.title}]] <!-- ref: ${carriedTask2.id} -->
- [x] [[${doneTask.relativeLink}|${doneTask.title}]] <!-- ref: ${doneTask.id} -->
`
  );

  return { vaultRoot, taskRegistry, carriedTasks: [carriedTask1, carriedTask2] };
}

export async function runStartupBenchmark() {
  await mkdir('.temp', { recursive: true });
  const tempRoot = await realpath(await mkdtemp(path.resolve('.temp/startup-eval-')));
  const now = '2026-10-19T10:00:00.000Z';
  const cliPath = path.resolve('src/cli/daily-tasks.mjs');

  try {
    const { vaultRoot, taskRegistry, carriedTasks } = await createBenchmarkVault(tempRoot, now);
    const inputFile = path.join(tempRoot, 'input.json');
    const outputFile = path.join(tempRoot, 'output.json');
    await writeFile(inputFile, JSON.stringify({ vaultRoot, now }), 'utf8');

    // --- CHECK 1: Health-Check ---
    const t0Health = performance.now();
    const healthResult = await execute(process.execPath, [cliPath, 'health-check', '--input', inputFile]);
    const t1Health = performance.now();
    const healthData = JSON.parse(healthResult.stdout);
    if (healthData.status !== 'ok' || !healthData.configured) {
      throw new Error(`Health check failed: ${JSON.stringify(healthData)}`);
    }
    const healthElapsed = Math.round(t1Health - t0Health);

    // --- CHECK 2: Windows UTF-16LE BOM Input Resilience ---
    const bomInputFile = path.join(tempRoot, 'input-bom.json');
    const utf16leBytes = Buffer.concat([Buffer.from([0xFF, 0xFE]), Buffer.from(JSON.stringify({ vaultRoot, now }), 'utf16le')]);
    await writeFile(bomInputFile, utf16leBytes);
    const bomResult = await execute(process.execPath, [cliPath, 'health-check', '--input', bomInputFile]);
    const bomData = JSON.parse(bomResult.stdout);
    if (bomData.status !== 'ok') {
      throw new Error('UTF-16LE BOM decoding failed on --input');
    }

    // --- CHECK 3: Planning-Prepare Latency & Complete Projection ---
    const t0Prepare = performance.now();
    await execute(process.execPath, [cliPath, 'planning-prepare', '--input', inputFile, '--output', outputFile]);
    const t1Prepare = performance.now();
    const prepareElapsed = Math.round(t1Prepare - t0Prepare);

    const prepareData = JSON.parse(await readFile(outputFile, 'utf8'));

    if (prepareElapsed > LATENCY_BUDGET_MS) {
      throw new Error(`Latency budget exceeded: ${prepareElapsed}ms > ${LATENCY_BUDGET_MS}ms budget`);
    }
    if (prepareData.status !== 'create-plan' && prepareData.status !== 'prepared') {
      throw new Error(`Unexpected prepare status: ${prepareData.status}`);
    }
    if (!prepareData.current?.proposedId) {
      throw new Error('Expected proposedId on unwritten daily plan');
    }
    if (prepareData.inventory?.tasks?.length !== 40) {
      throw new Error(`Expected 40 indexed tasks, got ${prepareData.inventory?.tasks?.length}`);
    }
    if (prepareData.rollover?.status !== 'due') {
      throw new Error(`Expected rollover.status 'due', got '${prepareData.rollover?.status}'`);
    }
    if (!Array.isArray(prepareData.rollover?.selected) || prepareData.rollover.selected.length === 0) {
      throw new Error('Expected pre-computed rollover.selected candidates');
    }
    if (!Array.isArray(prepareData.rollover?.taskSources) || prepareData.rollover.taskSources.length === 0) {
      throw new Error('Expected pre-computed rollover.taskSources hashes');
    }
    for (const source of prepareData.rollover.taskSources) {
      if (!source.path || !/^[a-f0-9]{64}$/.test(source.sha256)) {
        throw new Error(`Invalid taskSource entry: ${JSON.stringify(source)}`);
      }
    }
    if (!prepareData.review?.selected || prepareData.review.selected.length === 0) {
      throw new Error('Expected pre-computed review.selected');
    }

    // --- CHECK 4: Single-Pass Plan Authoring & Review Screen Validation ---
    const todayDate = '2026.10.19';
    const planPath = path.join(vaultRoot, '2-areas', 'daily-plans', `${todayDate}-daily-plan.md`);
    const planRows = prepareData.rollover.selected.map(item => {
      const reg = taskRegistry.find(t => t.id === item.id);
      return `- [ ] ↺ [[${reg?.relativeLink ?? item.target ?? 'task'}|${item.title}]] <!-- ref: ${item.id} -->`;
    });
    const planMarkdown = `---
id: ${prepareData.current.proposedId}
type: daily-plan
created_at: ${now}
---
# Today's Plan

${planRows.join('\n')}
`;
    await writeFile(planPath, planMarkdown, 'utf8');

    // Run planning-prepare again; should transition to 'prepared'
    await execute(process.execPath, [cliPath, 'planning-prepare', '--input', inputFile, '--output', outputFile]);
    const reopenedData = JSON.parse(await readFile(outputFile, 'utf8'));
    if (reopenedData.status !== 'prepared') {
      throw new Error(`Expected status 'prepared' after plan authoring, got '${reopenedData.status}'`);
    }

    // Call planning-state save-review on the authored review screen
    const reviewMarkdown = planningScreen(reopenedData);
    const stateInputFile = path.join(tempRoot, 'state-input.json');
    await writeFile(
      stateInputFile,
      JSON.stringify({
        vaultRoot,
        now,
        action: 'save-review',
        reviewMarkdown,
        expectedPlanHash: reopenedData.current.sha256,
        expectedPreviousHash: reopenedData.previous?.sha256 ?? null,
        expectedStateHash: null,
        expectedInventoryHash: reopenedData.inventoryHash,
        expectedReviewHash: reopenedData.reviewHash,
      }),
      'utf8'
    );

    const saveResult = await execute(process.execPath, [cliPath, 'planning-state', '--input', stateInputFile]);
    const saveData = JSON.parse(saveResult.stdout);
    if (saveData.status !== 'saved') {
      throw new Error(`Single-pass save-review failed: ${JSON.stringify(saveData)}`);
    }

    return {
      status: 'pass',
      healthElapsed,
      prepareElapsed,
      tasksIndexed: prepareData.inventory.tasks.length,
      rolloverSelected: prepareData.rollover.selected.length,
      taskSources: prepareData.rollover.taskSources.length,
    };
  } finally {
    await rm(tempRoot, { recursive: true, force: true }).catch(() => {});
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === path.resolve(new URL(import.meta.url).pathname.replace(/^\/([A-Z]:)/, '$1'))) {
  runStartupBenchmark().then(result => {
    console.log(`✓ Health-Check: ${result.healthElapsed}ms`);
    console.log(`✓ UTF-16LE BOM Decoding: verified`);
    console.log(`✓ Planning-Prepare Latency: ${result.prepareElapsed}ms (budget: ${LATENCY_BUDGET_MS}ms)`);
    console.log(`✓ Complete Projection: ${result.tasksIndexed} tasks, ${result.rolloverSelected} rollover items, ${result.taskSources} task sources`);
    console.log(`✓ Single-Pass Authoring & Screen Validation: 0 repair loops (status: saved)`);
    console.log(`\nSTARTUP EVAL PASSED`);
  }).catch(error => {
    console.error(`\n✖ STARTUP EVAL FAILED: ${error.message}`);
    process.exitCode = 1;
  });
}
