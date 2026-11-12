"""Responsibility: Compute how much of a milestone's work is finished.
Public interface:
`-- milestone_completion_percent(facts)

Milestone completion percentage from its task counts.
"""

from daily_tasks.core.records.milestone_facts import MilestoneFacts


def milestone_completion_percent(facts: MilestoneFacts) -> float:
    """Return finished tasks as a percentage of counted tasks, rounded to one decimal; 0.0 without tasks."""
    if not facts.tasks_total:
        return 0.0
    return round((facts.tasks_total - facts.tasks_open) * 100 / facts.tasks_total, 1)
