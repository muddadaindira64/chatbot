from pydantic import BaseModel, Field


class ChatToolResponse(BaseModel):
    name: str | None = None
    input: str | None = None
    output: str | None = None
    requires_tool: bool = False


class ChatRequest(BaseModel):
    conversation_id: int | None = Field(None, description="Conversation ID for existing chat")
    message: str = Field(min_length=1, max_length=4000)


class ChatResponse(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    tool: ChatToolResponse | None = None
    requires_tool: bool = False
    conversation_id: int | None = None
    message_id: int | None = None


class NewChatResponse(BaseModel):
    conversation_id: int
    message: str
