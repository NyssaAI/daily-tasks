import test from 'node:test';
import assert from 'node:assert/strict';
import { cp, mkdir, mkdtemp, readFile, readdir, realpath, writeFile } from 'node:fs/promises';
import { execFile } from 'node:child_process';
import { promisify } from 'node:util';
import path from 'node:path';

const exec = promisify(execFile);
const repo = path.resolve('.');
for (const group of ['activation','content']) {
  for (const name of await readdir(path.join(repo,'evals/tessl',group))) {
    test(`Tessl ${group}/${name} transports a working template and planning runtime`, async () => {
      const scenarioRoot = path.join(repo,'evals/tessl',group,name);
      const scenario = JSON.parse(await readFile(path.join(scenarioRoot,'scenario.json'),'utf8'));
      const setup = await readFile(path.join(scenarioRoot,'setup.sh'),'utf8');
      const mode = /node support\/evals\/tessl\/fixture.mjs (\w+)/.exec(setup)?.[1];
      assert.ok(mode);
      await mkdir(path.join(repo,'.temp'),{recursive:true});
      const sandbox = await realpath(await mkdtemp(path.join(repo,'.temp/tessl-fixture-')));
      const support = scenario.fixtures.support;
      const source = path.resolve(scenarioRoot,support.path);
      for (const member of support.include) {
        const relative = member.replace(/\/\*\*$/,'');
        const destination = path.join(sandbox,support.installPath,relative);
        await mkdir(path.dirname(destination),{recursive:true});
        await cp(path.join(source,relative),destination,{recursive:true});
      }
      await exec(process.execPath,['support/evals/tessl/fixture.mjs',mode],{cwd:sandbox});
      const environment = JSON.parse(await readFile(path.join(sandbox,'ENVIRONMENT.md'),'utf8'));
      const inputPath = path.join(sandbox,'input.json');
      await writeFile(inputPath,JSON.stringify({...environment,homeRoot:environment.homeRoot ?? path.join(sandbox,'synthetic-home'),kinds:['dailyPlan','planDayReview']}));
      const command = path.join(sandbox,'support/src/cli/daily-tasks.mjs');
      const planning = JSON.parse((await exec(process.execPath,[command,'planning-prepare','--input',inputPath,'--dry-run'],{cwd:repo,maxBuffer:4*1024*1024})).stdout);
      if (mode === 'fresh') assert.equal(planning.status,'setup-required');
      else {
        assert.notEqual(planning.status,'setup-required');
        const templates = JSON.parse((await exec(process.execPath,[command,'template-prepare','--input',inputPath,'--dry-run'],{cwd:repo})).stdout);
        assert.ok(templates.templates.dailyPlan.active.content.length > 0);
        assert.ok(templates.templates.planDayReview.active.content.length > 0);
      }
      await assert.rejects(readFile(path.join(sandbox,'support/skills/daily-tasks/SKILL.md')), {code:'ENOENT'});
    });
  }
}
