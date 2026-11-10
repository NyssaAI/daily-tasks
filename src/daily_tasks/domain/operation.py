"""Responsibility: Represent an immutable Operation DTO.
Public interface:
`-- Operation

Operation DTO.
"""

from typing import Annotated

from pydantic import Field

from daily_tasks.domain.assign_to_day import AssignToDay
from daily_tasks.domain.reassign import Reassign
from daily_tasks.domain.set_status import SetStatus
from daily_tasks.domain.unplan import Unplan

type Operation = Annotated[AssignToDay | Unplan | SetStatus | Reassign, Field(discriminator="kind")]
