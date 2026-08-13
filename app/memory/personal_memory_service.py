from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models import PersonalMemory


async def get_personal_memories_for_user(
    db: AsyncSession,
    user_id: int,
) -> list[PersonalMemory]:
    result = await db.execute(
        select(PersonalMemory)
        .where(PersonalMemory.user_id == user_id)
        .order_by(PersonalMemory.updated_at.desc())
    )
    return list(result.scalars().all())


async def upsert_personal_memory(
    db: AsyncSession,
    user_id: int,
    key: str,
    value: str,
) -> PersonalMemory:
    if not key or not value:
        raise ValueError("Memory key and value are required")

    result = await db.execute(
        select(PersonalMemory).where(
            PersonalMemory.user_id == user_id,
            PersonalMemory.key == key,
        )
    )
    memory = result.scalar_one_or_none()

    if memory is None:
        memory = PersonalMemory(user_id=user_id, key=key, value=value)
        db.add(memory)
    else:
        memory.value = value

    await db.commit()
    await db.refresh(memory)
    return memory


async def get_personal_memory_context(
    db: AsyncSession,
    user_id: int,
) -> str:
    memories = await get_personal_memories_for_user(db, user_id)
    if not memories:
        return ""

    lines = []
    for memory in memories:
        lines.append(f"{memory.key}: {memory.value}")

    return "User Personal Memory:\n" + "\n".join(lines)
