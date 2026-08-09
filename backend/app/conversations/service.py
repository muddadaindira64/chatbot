from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import (
    Conversation,
    Message
)



# =========================
# CREATE NEW CHAT / THREAD
# =========================

async def create_conversation(
    db: AsyncSession,
    user_id: int,
    title: str = "New Chat"
) -> Conversation:

    conversation = Conversation(
        user_id=user_id,
        title=title
    )

    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return conversation


async def create_new_conversation(
    db: AsyncSession,
    user_id: int,
    title: str = "New Chat"
) -> Conversation:
    """
    Create a new conversation for a user.
    Alias for create_conversation for clarity.
    """
    return await create_conversation(db, user_id, title)



# =========================
# GET CONVERSATIONS
# =========================

async def get_user_conversations(
    db: AsyncSession,
    user_id: int
) -> list[Conversation]:

    result = await db.execute(
        select(Conversation)
        .join(Message)
        .where(
            Conversation.user_id == user_id,
            Message.role.in_(["user", "assistant"]),
        )
        .distinct()
        .order_by(Conversation.created_at.desc())
    )
    return result.scalars().all()



# =========================
# GET SINGLE CONVERSATION
# =========================

async def get_conversation(
    db: AsyncSession,
    conversation_id: int,
    user_id: int
) -> Conversation | None:

    result = await db.execute(
        select(Conversation)
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id
        )
    )
    return result.scalar_one_or_none()


async def update_conversation_title(
    db: AsyncSession,
    conversation_id: int,
    user_id: int,
    title: str,
) -> Conversation | None:
    conversation = await get_conversation(db, conversation_id, user_id)
    if not conversation:
        return None

    conversation.title = title
    await db.commit()
    await db.refresh(conversation)
    return conversation


async def delete_conversation(
    db: AsyncSession,
    conversation_id: int,
    user_id: int,
) -> bool:
    conversation = await get_conversation(db, conversation_id, user_id)
    if not conversation:
        return False

    await db.delete(conversation)
    await db.commit()
    return True


# =========================
# SAVE MESSAGE
# =========================

async def add_message_to_conversation(
    db: AsyncSession,
    conversation_id: int,
    role: str,
    content: str
) -> Message:

    message = Message(
        conversation_id=conversation_id,
        role=role,
        content=content
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    return message



# =========================
# GET CHAT HISTORY
# =========================

async def get_conversation_history(
    db: AsyncSession,
    user_id: int,
    conversation_id: int | None = None,
    limit: int = 20
) -> list[dict]:
    """
    Get conversation history.
    If conversation_id is provided, get messages for that specific conversation.
    Otherwise, get recent messages from all user conversations.
    """
    query = (
        select(Message)
        .join(Conversation)
        .where(
            Conversation.user_id == user_id,
            Message.role.in_(["user", "assistant"]),
        )
    )
    
    # If conversation_id is provided, filter by it
    if conversation_id:
        query = query.where(Message.conversation_id == conversation_id)
    
    query = query.order_by(Message.created_at.desc()).limit(limit)
    
    result = await db.execute(query)
    messages = result.scalars().all()
    
    # Reverse to get chronological order
    messages = list(reversed(messages))
    
    return [
        {
            "role": msg.role,
            "content": msg.content
        }
        for msg in messages
    ]
