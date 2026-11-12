"""Responsibility: Represent an immutable ToolResults DTO.
Public interface:
`-- ToolResults

ToolResults DTO.
"""

from daily_tasks.core.planning.tool_result import ToolResult

type ToolResults = tuple[ToolResult, ...]
