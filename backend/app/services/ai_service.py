import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any

from fastapi import HTTPException, status
from langchain_core.messages import AIMessage, BaseMessage

from app.core.config import settings
from app.prompts.chat_prompt import build_messages, build_prompt
from app.services.llm_service import LLMService



logger = logging.getLogger(__name__)


class AIService:

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.llm_service = LLMService()

    # =====================================================================
    # Legacy helpers (kept for backward compatibility with existing callers)
    # =====================================================================

    async def complete(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tool: dict[str, Any] | None = None,
    ) -> str:
        if not self.api_key:
            logger.error("OpenRouter API key is missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        try:
            prompt = build_prompt(
                user_message=message,
                context=context,
                history=history,
                tool=tool,
            )
        except ValueError as exc:
            logger.exception("Prompt generation failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        try:
            response = self.llm_service.invoke(prompt)
            return response.content or ""
        except Exception as exc:
            logger.exception("OpenRouter completion failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Workflow execution failed while calling OpenRouter.",
            ) from exc

    async def stream_complete(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tool: dict[str, Any] | None = None,
    ) -> AsyncGenerator[str, None]:
        if not self.api_key:
            logger.error("OpenRouter API key is missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        try:
            prompt = build_prompt(
                user_message=message,
                context=context,
                history=history,
                tool=tool,
            )
        except ValueError as exc:
            logger.exception("Prompt generation failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        try:
            for chunk in self.llm_service.stream(prompt):
                yield chunk
        except Exception as exc:
            logger.exception("OpenRouter streaming failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Streaming response failed while calling OpenRouter.",
            ) from exc
    async def complete_json(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tool: dict[str, Any] | None = None,
    ) -> str:
        if not self.api_key:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        prompt = build_prompt(
            user_message=message,
            context=context,
            history=history,
            tool=tool,
        )

        try:
            response = self.llm_service.invoke(prompt)

            return response.content or ""

        except Exception as exc:
            logger.exception("OpenRouter completion failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="LLM response generation failed.",
            ) from exc
    # =====================================================================
    # Native LangChain Tool Calling helpers
    # =====================================================================

    def invoke_with_tools(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tool_messages: list[BaseMessage] | None = None,
        ai_tool_message: AIMessage | None = None,
    ) -> AIMessage:
        """
        Invoke the LLM with native tool calling.

        The LLM decides automatically which tool to call (if any).
        The returned AIMessage exposes `.tool_calls` when a tool is needed.
        """
        if not self.api_key:
            logger.error("OpenRouter API key is missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        try:
            messages = build_messages(
                user_message=message,
                context=context,
                history=history,
                tool_messages=tool_messages,
                ai_tool_message=ai_tool_message,
            )
        except ValueError as exc:
            logger.exception("Message build failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        try:
            return self.llm_service.invoke_with_tools(messages)
        except Exception as exc:
            logger.exception("OpenRouter tool-calling invocation failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Workflow execution failed while calling OpenRouter.",
            ) from exc

    def stream_with_tools(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
        tool_messages: list[BaseMessage] | None = None,
        ai_tool_message: AIMessage | None = None,
    ) -> Generator[Any, None, None]:
        """
        Stream the LLM with native tool calling.

        Yields raw AIMessageChunk objects from the LLM so the caller can:
        - Stream content chunks directly to the client.
        - Detect or aggregate native tool_call_chunks.

        The LLM decides automatically which tool to call (if any).
        """
        if not self.api_key:
            logger.error("OpenRouter API key is missing")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )

        try:
            messages = build_messages(
                user_message=message,
                context=context,
                history=history,
                tool_messages=tool_messages,
                ai_tool_message=ai_tool_message,
            )
        except ValueError as exc:
            logger.exception("Message build failed")
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc

        try:
            return self.llm_service.stream_with_tools(messages)
        except Exception as exc:
            logger.exception("OpenRouter tool-calling streaming failed")
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Streaming response failed while calling OpenRouter.",
            ) from exc
