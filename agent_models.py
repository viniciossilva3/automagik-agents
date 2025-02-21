"""Models for agent responses."""
from typing import Optional
from pydantic import BaseModel, Field

class AgentResponse(BaseModel):
    """Response from the agent including reasoning and message."""
    reasoning: Optional[str] = Field(
        None,
        description="Thought process and reasoning about how to handle the request"
    )
    message: str = Field(
        ...,  # ... means required
        description="The actual response message that should be shown to the user"
    )
