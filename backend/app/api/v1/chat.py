import asyncio
import logging
import re
import time
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Request, status

from app.auth.dependencies import get_current_user_or_guest
from app.core.config import settings
from app.database.database import AsyncSessionLocal
from app.conversations.service import (
    add_message_to_conversation,
    create_new_conversation,
    get_conversation,
    get_conversation_history,
)
from app.database.database import get_db
from app.graph.workflow import ChatWorkflow
from app.memory.context import build_user_context
from app.memory.service import update_memory
from app.schemas.chat import ChatRequest, ChatResponse, NewChatResponse
from app.services.tool_executor import (
    build_frontend_tool_payload,
    execute_tool_calls,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


TOOL_NAME_MAP = {
    "search": "live_search",
    "calculator": "calculator",
    "weather": "get_weather",
}


def _format_tool_message(tool_result: dict[str, Any]) -> str:
    tool_used = tool_result.get("name")
    tool_input = tool_result.get("input") or ""
    tool_output = tool_result.get("output") or ""
    requires_tool = bool(tool_result.get("requires_tool"))

    if not tool_used or not requires_tool or tool_used == "none":
        return "Tool Used: None"

    return (
        f"Tool Used: {tool_used}\n"
        f"Tool Input: {tool_input}\n"
        f"Tool Output:\n{tool_output}"
    ).strip()


def _empty_tool_payload() -> dict[str, Any]:
    return {
        "name": "none",
        "input": None,
        "output": None,
        "requires_tool": False,
    }


def _response_tool_payload(frontend_tool: dict[str, Any]) -> dict[str, Any]:
    name = frontend_tool.get("name")
    if not name or name == "none":
        name = None

    return {
        "name": name,
        "input": frontend_tool.get("input"),
        "output": frontend_tool.get("output"),
    }


def _build_tool_call(tool_name: str, tool_input: str) -> tuple[dict[str, Any], str]:
    internal_name = TOOL_NAME_MAP[tool_name]
    tool_input = tool_input.strip()

    if tool_name == "search":
        args = {"query": tool_input}
    elif tool_name == "calculator":
        args = {"expression": tool_input}
    else:
        args = {"city": tool_input}

    return {
        "name": internal_name,
        "args": args,
        "id": f"call_{internal_name}_{int(time.time() * 1000)}",
    }, tool_input


async def _finish_and_evaluate(
    db,
    current_user,
    conversation_id: int,
    question: str,
    answer: str,
) -> int | None:
    """Save the assistant message and trigger background evaluation."""
    if not answer.strip():
        return None

    assistant_message = await add_message_to_conversation(
        db=db,
        conversation_id=conversation_id,
        role="assistant",
        content=answer.strip(),
    )
    logger.info("Assistant message saved")
    message_id = assistant_message.id

    logger.info("Evaluation started")

    async def run_evaluation():
        try:
            from app.evaluation.service import save_evaluation

            async with AsyncSessionLocal() as evaluation_db:
                await save_evaluation(
                    db=evaluation_db,
                    user_id=current_user.id,
                    conversation_id=conversation_id,
                    message_id=assistant_message.id,
                    question=question,
                    answer=answer.strip(),
                )
            logger.info("Evaluation completed")
        except Exception:
            logger.exception("Background evaluation failed")

    asyncio.create_task(run_evaluation())

    return message_id


async def generate_chat_response(
    request: ChatRequest,
    current_user,
    db,
    conversation_id: int,
) -> dict[str, Any]:
    """Generate one complete JSON chat response using router-selected tools."""
    started_at = time.perf_counter()
    stage = "starting"

    logger.info("Processing chat for conversation %s", conversation_id)

    try:
        stage = "loading_history"
        history = await get_conversation_history(
            db,
            current_user.id,
            conversation_id=conversation_id,
            limit=20,
        )
        logger.info("Conversation history loaded for conversation %s", conversation_id)

        stage = "saving_user_message"
        logger.info("Saving user message")
        await add_message_to_conversation(
            db=db,
            conversation_id=conversation_id,
            role="user",
            content=request.message,
        )
        logger.info("User message saved")


        stage = "generating_llm_response"
        workflow = ChatWorkflow()
        final_answer, used_tool_name, used_tool_output = await workflow.run(
            message=request.message,
            user_id=current_user.id,
            conversation_id=conversation_id,
            memory_context=None,
            history=history,
        )

        frontend_tool = _empty_tool_payload()
        if used_tool_name:
            frontend_tool = {
                "name": used_tool_name,
                "input": None,
                "output": used_tool_output,
                "requires_tool": True,
            }

        final_answer = (final_answer or "").strip() or "I could not generate a response. Please try again."

        message_id = await _finish_and_evaluate(
            db=db,
            current_user=current_user,
            conversation_id=conversation_id,
            question=request.message,
            answer=final_answer,
        )

        return {
            "message": final_answer,
            "tool": _response_tool_payload(frontend_tool),
            "requires_tool": bool(frontend_tool.get("requires_tool")),
            "conversation_id": conversation_id,
            "message_id": message_id,
        }

    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("Unexpected error while processing chat request at stage=%s", stage)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{exc.__class__.__name__}: {exc}",
        ) from exc
    finally:
        elapsed_ms = round((time.perf_counter() - started_at) * 1000, 2)
        logger.info("Chat request completed in %.2f ms", elapsed_ms)


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    http_request: Request,
    current_user=Depends(get_current_user_or_guest),
    db=Depends(get_db),
) -> dict[str, Any]:
    logger.info("Incoming chat request received at %s", http_request.url.path)

    try:
        if not settings.openrouter_api_key:
            logger.error("OpenRouter API key missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        conversation_id = request.conversation_id

        if conversation_id:
            logger.info("Looking up conversation %s for user %s", conversation_id, current_user.id)
            conversation = await get_conversation(db, conversation_id, current_user.id)
            if not conversation:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Conversation not found",
                )
        else:
            logger.info("Creating new conversation for user %s", current_user.id)
            conversation = await create_new_conversation(
                db=db,
                user_id=current_user.id,
                title=request.message[:50],
            )
            conversation_id = conversation.id

        logger.info("Conversation ready: %s", conversation_id)
        logger.info("Returning complete JSON response")
        return await generate_chat_response(
            request=request,
            current_user=current_user,
            db=db,
            conversation_id=conversation_id,
        )
    except HTTPException:
        raise
    except Exception as exc:
        logger.exception("chat_with_ai failed")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"{exc.__class__.__name__}: {exc}",
        ) from exc


@router.post("/new-chat", response_model=NewChatResponse)
async def new_chat(
    current_user=Depends(get_current_user_or_guest),
    db=Depends(get_db),
):
    logger.info("Creating new chat for user %s", current_user.id)
    conversation = await create_new_conversation(db, current_user.id)

    logger.info("New chat started for user %s", current_user.id)

    return NewChatResponse(
        conversation_id=conversation.id,
        message="New chat created"
    )
