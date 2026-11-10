"""Responsibility: Represent an immutable ToolResults DTO.
Public interface:
`-- ToolResults

ToolResults DTO.
"""

from daily_tasks.domain.tool_result import ToolResult

type ToolResults = tuple[ToolResult, ...]
