import logging
from typing import Any

from app.database.database import AsyncSessionLocal
from app.memory.service import update_memory

logger = logging.getLogger(__name__)


async def personal_memory_analyzer(state: dict[str, Any]) -> dict[str, Any]:
    """Analyze the latest user message and persist personal memories for the authenticated user."""
    messages = state.get("messages", []) or []
    user_id = state.get("user_id")
    conversation_id = state.get("conversation_id")

    latest_user_message = None
    for message in reversed(messages):
        message_type = getattr(message, "type", None)
        if message_type == "human":
            latest_user_message = message.content
            break

    logger.info(
        "memory_update user_id=%s conversation_id=%s message=%s",
        user_id,
        conversation_id,
        latest_user_message,
    )

    if not latest_user_message or not user_id:
        return {"messages": []}

    async with AsyncSessionLocal() as db:
        await update_memory(db, user_id, latest_user_message)

    logger.info("memory_update completed user_id=%s conversation_id=%s", user_id, conversation_id)
    return {"messages": []}
