# Responsibility: Represent an immutable DecisionOrigin DTO.
# Public interface:
# `-- DecisionOrigin
"""DecisionOrigin DTO."""

from typing import Annotated
from pydantic import Field
from daily_tasks.domain.instruction_origin import InstructionOrigin
from daily_tasks.domain.suggestion_origin import SuggestionOrigin


type DecisionOrigin = Annotated[SuggestionOrigin | InstructionOrigin, Field(discriminator="kind")]

