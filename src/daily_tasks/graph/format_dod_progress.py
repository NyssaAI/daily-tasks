# Responsibility: Present Definition of Done progress as a label and a ratio.
# Public interface:
# +-- dod_ratio(progress)
# `-- format_dod_progress(progress)
"""`done/total` labels and completion ratios for `DodProgress`."""

from daily_tasks.domain import DodProgress


def format_dod_progress(progress: DodProgress) -> str:
    """Return `done/total`, for example `1/2`."""
    return f"{progress.done}/{progress.total}"


def dod_ratio(progress: DodProgress) -> float:
    """Return done/total in [0, 1]; an empty Definition of Done counts as complete (1.0)."""
    return progress.done / progress.total if progress.total else 1.0
