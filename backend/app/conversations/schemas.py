from datetime import datetime

from pydantic import BaseModel, Field


class ConversationCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)


class ConversationResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: datetime


class MessageResponse(BaseModel):
    id: int
    conversation_id: int
    role: str
    content: str
    tool: str | None = None
    created_at: datetime
