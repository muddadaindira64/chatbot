from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from app.api.routes import router as api_router
from app.api.v1.chat import router as chat_router
from app.auth.router import router as auth_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import setup_logging
from app.database.database import Base, engine
import logging
from app.conversations.router import router as conversation_router
from app.feedback.router import router as feedback_router

logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

@asynccontextmanager
async def lifespan(_: FastAPI):
    setup_logging()
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        # Ensure existing SQLite schema includes tool_name on messages
        result = await conn.execute(
            text(
                "SELECT name FROM pragma_table_info('messages') WHERE name = 'tool_name';"
            )
        )
        if result.first() is None:
            await conn.execute(
                text(
                    "ALTER TABLE messages ADD COLUMN tool_name VARCHAR(100) NULL"
                )
            )
    yield


app = FastAPI(
    title=settings.app_name,
    description=settings.app_description,
    version=settings.app_version,
    debug=settings.debug,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in settings.allowed_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(auth_router, prefix=settings.api_prefix)
app.include_router(conversation_router)
app.include_router(feedback_router, prefix=settings.api_prefix)

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": settings.app_name,
        "version": settings.app_version,
    }
@app.get("/")
def home():
    return {"message":"running"}
