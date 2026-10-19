import { lstat, readFile, readdir } from 'node:fs/promises';
import path from 'node:path';

const fail = message => {
  console.error(message);
  process.exitCode = 1;
};

const workspace = process.env.WAZA_WORKSPACE_DIR;
if (!workspace) {
  fail('WAZA_WORKSPACE_DIR is unavailable; cannot validate the isolated setup result.');
} else {
  const home = path.join(workspace, 'synthetic-home');
  const config = path.join(home, '.nyssa-ai', 'daily-tasks');
  const profilePath = path.join(config, 'profile.json');
  const allowedFiles = new Set([
    'README.md',
    '.nyssa-ai/daily-tasks/profile.json',
  ]);
  const allowedDirectories = new Set([
    '.nyssa-ai',
    '.nyssa-ai/daily-tasks',
  ]);
  const files = [];
  const directories = [];

  async function walk(directory, relative = '') {
    for (const entry of await readdir(directory, { withFileTypes: true })) {
      const childRelative = relative ? `${relative}/${entry.name}` : entry.name;
      const childPath = path.join(directory, entry.name);
      if (entry.isSymbolicLink()) {
        fail(`Unexpected symbolic link in synthetic home: ${childRelative}`);
      } else if (entry.isDirectory()) {
        directories.push(childRelative);
        await walk(childPath, childRelative);
      } else if (entry.isFile()) {
        files.push(childRelative);
      } else {
        fail(`Unexpected filesystem entry in synthetic home: ${childRelative}`);
      }
    }
  }

  try {
    const workspaceEntries = await readdir(workspace);
    for (const entry of workspaceEntries) {
      if (entry !== 'synthetic-home') fail(`Unexpected workspace artifact: ${entry}`);
    }

    const homeStat = await lstat(home);
    if (!homeStat.isDirectory() || homeStat.isSymbolicLink()) {
      throw new Error('synthetic-home must be a real directory');
    }

    await walk(home);
    for (const file of files) {
      if (!allowedFiles.has(file)) fail(`Unexpected file in synthetic home: ${file}`);
    }
    for (const directory of directories) {
      if (!allowedDirectories.has(directory)) {
        fail(`Unexpected directory in synthetic home: ${directory}`);
      }
    }
    for (const expected of allowedFiles) {
      if (!files.includes(expected)) fail(`Required file is missing: ${expected}`);
    }
    for (const expected of allowedDirectories) {
      if (!directories.includes(expected)) fail(`Required directory is missing: ${expected}`);
    }

    const profileStat = await lstat(profilePath);
    if (!profileStat.isFile() || profileStat.isSymbolicLink()) {
      throw new Error('profile.json must be a regular file');
    }
    const profile = JSON.parse(await readFile(profilePath, 'utf8'));
    if (profile.schema_version !== 2) fail('New personal setup must save profile schema version 2.');
    const profileKeys = ['priorities', 'schema_version', 'timezone', 'user'];
    if (JSON.stringify(Object.keys(profile).sort()) !== JSON.stringify(profileKeys)) {
      fail(`Profile must contain only the requested personal settings: ${profileKeys.join(', ')}.`);
    }
    const userKeys = ['email', 'name'];
    if (JSON.stringify(Object.keys(profile.user ?? {}).sort()) !== JSON.stringify(userKeys)) {
      fail(`Profile user must contain only the requested name and email: ${userKeys.join(', ')}.`);
    }
    if (profile.user?.name !== 'Alex Example') fail('Saved user name does not match the request.');
    if (profile.user?.email !== 'alex@example.test') fail('Saved user email does not match the request.');
    if (profile.timezone !== 'America/Chicago') fail('Saved timezone does not match the requested IANA timezone.');
    if (!Array.isArray(profile.priorities) || profile.priorities.length !== 0) {
      fail('Saved priorities must be an empty list.');
    }

    if (process.exitCode !== 1) {
      console.log('Personal profile contents and isolated-home scope are valid.');
    }
  } catch (error) {
    fail(`Could not validate isolated personal setup: ${error.message}`);
  }
}
