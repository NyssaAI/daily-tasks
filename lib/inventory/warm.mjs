import { resolveContext } from '../profile/context.mjs';
import { projectInventory } from './inventory.mjs';

/**
 * Resolve the configured vault context, then invoke the ordinary stale-on-demand
 * inventory path. This operation never forces a refresh and returns no full inventory.
 */
export async function warmProjectIndex(input) {
  const context = await resolveContext(input);
  if (!context.configured || !context.vaultRoot || !context.projectsRoot || !context.dailyPlansRoot) {
    throw new Error('Configured vault context required for project-index prewarm');
  }
  const result = await projectInventory({
    vaultRoot:context.vaultRoot,
    projectsRoot:context.projectsRoot,
    dailyPlansRoot:context.dailyPlansRoot,
    homeRoot:context.homeRoot,
    timezone:context.timezone,
    ttlSeconds:context.ttlSeconds,
    now:context.now,
    dryRun:input.dryRun === true,
  });
  return {
    status:result.status,
    path:result.path,
    generatedAt:result.inventory.generatedAt,
    planningBinding:result.planningBinding,
    metrics:result.metrics,
    counts:{
      projects:result.inventory.projects.length,
      milestones:result.inventory.milestones.length,
      tasks:result.inventory.tasks.length,
      blockers:result.inventory.blockers.length,
      diagnostics:result.inventory.diagnostics.length,
    },
  };
}
