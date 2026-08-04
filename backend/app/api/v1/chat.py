import logging
import time

from fastapi import APIRouter, HTTPException, Request, status
from starlette.responses import StreamingResponse

from app.core.config import settings
from app.schemas.chat import ChatRequest
from app.services.ai_service import AIService

from app.memory.service import (
    get_memory_context,
    get_history,
    add_conversation,
    update_memory,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/chat")
async def chat_with_ai(
    request: ChatRequest,
    http_request: Request,
) -> StreamingResponse:

    started_at = time.perf_counter()

    logger.info(
        "Incoming chat request received at %s",
        http_request.url.path
    )


    # Check OpenRouter API key
    if not settings.openrouter_api_key:

        logger.error(
            "OpenRouter API key missing"
        )

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="OpenRouter API key is not configured."
        )


    try:

        # -------------------------------
        # MEMORY BEFORE LLM CALL
        # -------------------------------

        context = get_memory_context()

        history = get_history()


        logger.info(
            "Memory context loaded"
        )


        # -------------------------------
        # SAVE USER MESSAGE
        # -------------------------------

        add_conversation(
            role="user",
            content=request.message
        )


        # Extract user information
        update_memory(
            request.message
        )


        # -------------------------------
        # AI SERVICE
        # -------------------------------

        ai_service = AIService()


        response_stream = ai_service.stream_complete(
            message=request.message,
            context=context,
            history=history,
        )


        return StreamingResponse(
            response_stream,
            media_type="text/event-stream",
        )


    except HTTPException:
        raise


    except Exception as exc:

        logger.exception(
            "Unexpected error while processing chat request"
        )

        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unexpected chat processing error."
        ) from exc


    finally:

        elapsed_ms = round(
            (time.perf_counter() - started_at) * 1000,
            2
        )

        logger.info(
            "Chat request completed in %.2f ms",
            elapsed_ms
        )