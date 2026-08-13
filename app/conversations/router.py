from fastapi import APIRouter, Depends, HTTPException, status, Body
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_current_user
from app.conversations.service import (
    create_new_conversation,
    delete_conversation,
    get_conversation,
    get_user_conversations,
    update_conversation_title,
)
from app.database.database import get_db
from app.database.models import Message


router = APIRouter(
    prefix="/api/v1/conversations",
    tags=["Conversations"]
)


@router.get("")
async def list_conversations(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """List the current user's conversations (newest first)."""
    conversations = await get_user_conversations(db, current_user.id)

    return [
        {
            "id": conv.id,
            "conversation_id": conv.id,
            "title": conv.title,
            "created_at": conv.created_at,
        }
        for conv in conversations
    ]


@router.post("")
async def new_conversation(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Create a new conversation for the current user."""
    conversation = await create_new_conversation(
        db=db,
        user_id=current_user.id,
        title="New Chat",
    )

    return {
        "id": conversation.id,
        "conversation_id": conversation.id,
        "title": conversation.title,
    }


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: int,
    title: str = Body(..., embed=True),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    updated = await update_conversation_title(db, conversation_id, current_user.id, title)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return {
        "id": updated.id,
        "conversation_id": updated.id,
        "title": updated.title,
        "created_at": updated.created_at,
    }


@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    deleted = await delete_conversation(db, conversation_id, current_user.id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found")

    return {"deleted": True}


@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_user),
):
    """Get all messages for a specific conversation in chronological order."""
    conversation = await get_conversation(db, conversation_id, current_user.id)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    result = await db.execute(
        select(Message)
        .where(Message.conversation_id == conversation_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return [
        {
            "id": msg.id,
            "conversation_id": msg.conversation_id,
            "role": msg.role,
            "content": msg.content,
            "tool": msg.tool_name,
            "created_at": msg.created_at,
        }
        for msg in messages
    ]