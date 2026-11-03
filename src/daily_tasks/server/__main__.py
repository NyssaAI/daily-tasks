# Responsibility: Run the MCP stdio server with `python -m daily_tasks.server`.
# Public interface:
# (none)
"""Module entry point; same as the `daily-tasks-mcp` console script."""

import sys

from daily_tasks.cli import main

sys.exit(main())
