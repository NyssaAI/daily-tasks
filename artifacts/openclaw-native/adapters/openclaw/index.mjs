import { definePluginEntry } from 'openclaw/plugin-sdk/plugin-entry';
import { registerDailyTasksCli } from './cli.mjs';

export default definePluginEntry({
  id:'daily-tasks-openclaw',
  name:'Daily Tasks OpenClaw adapter',
  description:'Optional deterministic project-index prewarm automation setup.',
  register(api) {
    api.registerCli(async ({program,config}) => registerDailyTasksCli({program,pluginRoot:api.rootDir,gatewayConfig:config.gateway}), {
      descriptors:[{
        name:'daily-tasks',
        description:'Manage Daily Tasks OpenClaw integrations',
        hasSubcommands:true,
        machineOutput:() => true,
      }],
    });
  },
});
