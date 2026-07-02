from typing import List, Optional

from pydantic import BaseModel, Field

from app.models.requirement import Requirement
from app.state_machine.state import ConversationState


class ConversationContext(BaseModel):

    # conversation state
    state: ConversationState = ConversationState.START

    # extracted requirement accumulated over turns
    requirements: Requirement = Field(default_factory=Requirement)

    # conversation history
    history: List[str] = Field(default_factory=list)

    # number of turns
    turns: int = 0

    # whether recommendation is completed
    completed: bool = False

    # optional session id
    session_id: Optional[str] = None