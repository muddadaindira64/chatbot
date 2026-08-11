from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import UserMemory
from app.memory.personal_memory_service import (
    get_personal_memory_context,
)


async def build_user_context(
    db: AsyncSession,
    user_id: int,
) -> str:
    """Build user-specific context for the authenticated user."""

    context_parts: list[str] = []

    result = await db.execute(
        select(UserMemory).where(
            UserMemory.user_id == user_id
        )
    )

    user_memory = result.scalar_one_or_none()

    if user_memory:
        if user_memory.name:
            context_parts.append(
                f"User's name: {user_memory.name}"
            )

        if user_memory.role:
            context_parts.append(
                f"User's role: {user_memory.role}"
            )

        if user_memory.company:
            context_parts.append(
                f"User's company: {user_memory.company}"
            )

        if user_memory.skills:
            context_parts.append(
                f"User's skills: {', '.join(user_memory.skills)}"
            )

        if user_memory.preferences:
            context_parts.append(
                f"User's preferences: {user_memory.preferences}"
            )

    personal_memory = await get_personal_memory_context(
        db,
        user_id,
    )

    if personal_memory:
        context_parts.append(
            f"Personal Memory:\n{personal_memory}"
        )

    return "\n\n".join(context_parts)