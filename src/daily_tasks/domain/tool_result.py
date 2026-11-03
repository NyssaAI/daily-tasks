# Responsibility: Represent an immutable ToolResult DTO.
# Public interface:
# `-- ToolResult
"""ToolResult DTO."""

from typing import Annotated

from pydantic import Field

from daily_tasks.domain.tool_result_error import ToolResultError
from daily_tasks.domain.tool_result_ok import ToolResultOk
from daily_tasks.domain.tool_result_processing import ToolResultProcessing
from daily_tasks.domain.tool_result_refused import ToolResultRefused

type ToolResult = Annotated[
    ToolResultProcessing | ToolResultOk | ToolResultRefused | ToolResultError, Field(discriminator="status")
]
