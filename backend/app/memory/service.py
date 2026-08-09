import logging
from sqlalchemy.ext.asyncio import AsyncSession

from app.memory.user_memory_service import (
    get_user_memory,
    update_user_memory,
    get_user_memory_context,
)
from app.memory.analyzer import analyze_personal_information
from app.memory.personal_memory_service import (
    get_personal_memories_for_user,
    upsert_personal_memory,
    get_personal_memory_context,
)

logger = logging.getLogger(__name__)


async def get_memory_context(
    db: AsyncSession,
    user_id: int
) -> str:
    """Get formatted personal memory context for AI prompts."""
    context = await get_personal_memory_context(db, user_id)
    logger.info("loaded_memory user_id=%s context=%s", user_id, context or "")
    return context


async def update_memory(
    db: AsyncSession,
    user_id: int,
    message: str
):
    """Extract and persist personal memories for the authenticated user."""
    try:
        analysis_result = await analyze_personal_information(message)

        if not analysis_result.get("is_personal", False):
            return

        extracted_data = analysis_result.get("data", {}) or {}
        if not extracted_data:
            return

        for key, value in extracted_data.items():
            if key == "preferences" and isinstance(value, dict):
                for preference_key, preference_value in value.items():
                    if preference_value is None:
                        continue
                    await upsert_personal_memory(
                        db,
                        user_id,
                        preference_key,
                        str(preference_value),
                    )
            elif key in {"name", "role", "company"} and value:
                await upsert_personal_memory(db, user_id, key, str(value))
            elif key == "skills" and isinstance(value, list):
                for skill in value:
                    if skill:
                        await upsert_personal_memory(db, user_id, "skill", str(skill))

        logger.info(
            "Updated personal memories for user %s with keys: %s",
            user_id,
            list(extracted_data.keys()),
        )
    except Exception as exc:
        logger.error("Failed to update memory: %s", exc)
