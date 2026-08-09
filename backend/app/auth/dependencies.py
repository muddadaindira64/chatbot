from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import decode_access_token, hash_password
from app.database.database import get_db
from app.database.models import User, UserMemory

security = HTTPBearer(
    scheme_name="JWTBearer",
    description="Paste the JWT access token returned by POST /api/v1/auth/login. In Swagger UI, click Authorize and enter: Bearer <token>.",
)
optional_security = HTTPBearer(
    auto_error=False,
    scheme_name="JWTBearer",
)

GUEST_USERNAME = "__guest_chatbot__"
GUEST_EMAIL = "guest@chat.local"
GUEST_PASSWORD = "guest-chatbot-session"


async def _get_user_from_token(token: str, db: AsyncSession) -> User:
    payload = decode_access_token(token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = payload.get("user_id")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


async def get_or_create_guest_user(db: AsyncSession) -> User:
    result = await db.execute(
        select(User).where(
            (User.username == GUEST_USERNAME) | (User.email == GUEST_EMAIL)
        )
    )
    guest_user = result.scalar_one_or_none()

    if guest_user:
        return guest_user

    guest_user = User(
        username=GUEST_USERNAME,
        email=GUEST_EMAIL,
        password_hash=hash_password(GUEST_PASSWORD),
    )
    db.add(guest_user)
    await db.flush()

    db.add(
        UserMemory(
            user_id=guest_user.id,
            skills=[],
            preferences={},
        )
    )
    await db.commit()
    await db.refresh(guest_user)
    return guest_user


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Dependency to get the current authenticated user from JWT token.
    Raises HTTPException if token is invalid or user not found.
    """
    return await _get_user_from_token(credentials.credentials, db)


async def get_current_user_or_guest(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Return the authenticated user when a JWT token is provided.
    Fall back to a shared guest user when no token is supplied.
    """
    if credentials is None:
        return await get_or_create_guest_user(db)

    return await _get_user_from_token(credentials.credentials, db)
