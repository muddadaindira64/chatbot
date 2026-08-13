from pydantic import BaseModel, Field
from typing import List, Optional

class UserMemory(BaseModel):
    name: Optional[str] = None
    role: Optional[str] = None
    company: Optional[str] = None

    skills: List[str] = Field(default_factory=list)
    projects: List[str] = Field(default_factory=list)

    preferences: dict = Field(default_factory=dict)



class ConversationMessage(BaseModel):
    role: str
    content: str


class MemoryStore(BaseModel):
    user_memory: UserMemory = Field(default_factory=UserMemory)

    history: List[ConversationMessage] = Field(
        default_factory=list
    )