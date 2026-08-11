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
        logger.info("MEMORY_UPDATE_START user_id=%s message=%s", user_id, message)
        analysis_result = await analyze_personal_information(message)
        logger.info("MEMORY_ANALYZER_RESULT user_id=%s result=%s", user_id, analysis_result)

        if not analysis_result.get("is_personal", False):
            logger.info("MEMORY_NOT_PERSONAL user_id=%s message=%s", user_id, message)
            return

        # Handle both formats:
        # 1. New key/value format: {"is_personal": true, "key": "name", "value": "Guna"}
        # 2. Legacy data dict format: {"is_personal": true, "data": {"name": "Guna"}}
        extracted_data = {}

        key = analysis_result.get("key")
        value = analysis_result.get("value")

        if key and value is not None:
            extracted_data = {str(key): value}
        else:
            extracted_data = analysis_result.get("data", {}) or {}

        if not extracted_data:
            logger.info("MEMORY_NO_DATA user_id=%s", user_id)
            return

        for key, value in extracted_data.items():
            if key == "preferences" and isinstance(value, dict):
                for preference_key, preference_value in value.items():
                    if preference_value is None:
                        continue
                    logger.info("MEMORY_UPSERT user_id=%s key=%s value=%s", user_id, preference_key, str(preference_value))
                    await upsert_personal_memory(
                        db,
                        user_id,
                        preference_key,
                        str(preference_value),
                    )
            elif key in {"name", "role", "company"} and value:
                logger.info("MEMORY_UPSERT user_id=%s key=%s value=%s", user_id, key, str(value))
                await upsert_personal_memory(db, user_id, key, str(value))
            elif key == "skills" and isinstance(value, list):
                for skill in value:
                    if skill:
                        logger.info("MEMORY_UPSERT user_id=%s key=skill value=%s", user_id, str(skill))
                        await upsert_personal_memory(db, user_id, "skill", str(skill))
            else:
                # Generic personal memory (e.g. location, preferences, any other key)
                logger.info("MEMORY_UPSERT user_id=%s key=%s value=%s", user_id, key, str(value))
                await upsert_personal_memory(db, user_id, str(key), str(value))

        logger.info(
            "Updated personal memories for user %s with keys: %s",
            user_id,
            list(extracted_data.keys()),
        )
    except Exception as exc:
        logger.error("Failed to update memory: %s", exc)
