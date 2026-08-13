from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import Optional, Dict, Any

from app.database.models import UserMemory


async def get_user_memory(db: AsyncSession, user_id: int) -> Optional[UserMemory]:
    """
    Fetch user memory for a specific user.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        UserMemory object or None if not found
    """
    result = await db.execute(
        select(UserMemory).where(UserMemory.user_id == user_id)
    )
    return result.scalar_one_or_none()


async def update_user_memory(
    db: AsyncSession,
    user_id: int,
    data: Dict[str, Any]
) -> UserMemory:
    """
    Create or update user personal information.
    
    Args:
        db: Database session
        user_id: User ID
        data: Dictionary containing user memory fields to update
              (name, role, company, skills, preferences)
        
    Returns:
        Updated UserMemory object
    """
    # Fetch existing user memory
    result = await db.execute(
        select(UserMemory).where(UserMemory.user_id == user_id)
    )
    user_memory = result.scalar_one_or_none()
    
    if not user_memory:
        # Create new user memory if it doesn't exist
        user_memory = UserMemory(
            user_id=user_id,
            name=data.get("name"),
            role=data.get("role"),
            company=data.get("company"),
            skills=data.get("skills", []),
            preferences=data.get("preferences", {})
        )
        db.add(user_memory)
    else:
        # Update existing user memory
        if "name" in data:
            user_memory.name = data["name"]
        if "role" in data:
            user_memory.role = data["role"]
        if "company" in data:
            user_memory.company = data["company"]
        if "skills" in data:
            # Merge skills - add new ones, avoid duplicates
            existing_skills = set(user_memory.skills or [])
            new_skills = set(data["skills"])
            user_memory.skills = list(existing_skills.union(new_skills))
        if "preferences" in data:
            # Merge preferences
            existing_prefs = user_memory.preferences or {}
            existing_prefs.update(data["preferences"])
            user_memory.preferences = existing_prefs
    
    await db.commit()
    await db.refresh(user_memory)
    
    return user_memory


async def get_user_memory_context(db: AsyncSession, user_id: int) -> str:
    """
    Get formatted user memory context for AI prompts.
    
    Args:
        db: Database session
        user_id: User ID
        
    Returns:
        Formatted string with user information
    """
    user_memory = await get_user_memory(db, user_id)
    
    if not user_memory:
        return "No user information available."
    
    context_parts = []
    
    if user_memory.name:
        context_parts.append(f"Name: {user_memory.name}")
    if user_memory.role:
        context_parts.append(f"Role: {user_memory.role}")
    if user_memory.company:
        context_parts.append(f"Company: {user_memory.company}")
    if user_memory.skills:
        context_parts.append(f"Skills: {', '.join(user_memory.skills)}")
    
    if context_parts:
        return "User Information:\n" + "\n".join(context_parts)
    else:
        return "No user information available."