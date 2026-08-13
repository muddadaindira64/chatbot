from pydantic import BaseModel, Field
from datetime import datetime


class FeedbackCreate(BaseModel):
    """Schema for creating feedback."""
    message_id: int = Field(..., description="Message ID to provide feedback for")
    rating: str = Field(..., pattern="^(positive|negative)$", description="Rating: positive or negative")
    comment: str | None = Field(None, max_length=500, description="Optional comment")


class FeedbackResponse(BaseModel):
    """Schema for feedback response."""
    id: int
    user_id: int
    conversation_id: int
    message_id: int
    rating: str
    comment: str | None
    created_at: datetime

    class Config:
        from_attributes = True