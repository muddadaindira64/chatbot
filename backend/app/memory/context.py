from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.personal_memory_service import get_personal_memory_context


async def build_user_context(db: AsyncSession, user_id: int) -> str:
    """Build formatted context from that user's personal memories for LLM prompts."""
    return await get_personal_memory_context(db, user_id)