import logging
from collections.abc import AsyncGenerator, Generator
from typing import Any
import asyncio
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.mcp_tools import (
    mcp_calculator,
    mcp_search,
    mcp_weather,
    mcp_time_date,
)

logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

        self.client: BaseChatModel | None = None
        self.tools_client: BaseChatModel | None = None

    # =========================================================
    # NORMAL LLM CLIENT
    # Used for final answer generation and streaming
    # =========================================================

    def get_client(self) -> BaseChatModel:

        if self.client is None:

            if not self.api_key:
                raise ValueError(
                    "OpenRouter API key is missing"
                )

            self.client = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url,

                # Keep temperature low for accurate answers
                temperature=0.1,

                # Maximum output tokens
                max_tokens=4096,

                timeout=180,

                # Enable streaming
                streaming=True,
            )

            logger.info(
                "Normal LLM client initialized: model=%s max_tokens=%s",
                self.model,
                4096,
            )

        return self.client

    # =========================================================
    # TOOL ENABLED LLM CLIENT
    # Used ONLY for deciding/calling MCP tools
    # =========================================================

    def get_tools_client(self) -> BaseChatModel:

        if self.tools_client is None:

            mcp_tools = [
                mcp_calculator,
                mcp_search,
                mcp_weather,
                mcp_time_date,
            ]

            self.tools_client = (
                self.get_client()
                .bind_tools(
                    mcp_tools
                )
            )

            logger.info(
                "Tools bound: %s",
                [
                    tool.name
                    for tool in mcp_tools
                ],
            )

        return self.tools_client

    # =========================================================
    # ASYNC TOOL INVOCATION
    # =========================================================

    async def ainvoke_with_tools(
        self,
        messages: list[BaseMessage],
    ):

        llm = self.get_tools_client()

        logger.info(
            "Calling LLM with MCP tools"
        )

        response = await llm.ainvoke(
            messages
        )

        logger.info(
            "AI tool calls: %s",
            getattr(
                response,
                "tool_calls",
                None,
            ),
        )

        return response

    # =========================================================
    # SYNC TOOL INVOCATION
    # =========================================================

    def invoke_with_tools(
        self,
        messages: list[BaseMessage],
    ):

        llm = self.get_tools_client()

        logger.info(
            "Calling LLM with MCP tools"
        )

        response = llm.invoke(
            messages
        )

        logger.info(
            "AI tool calls: %s",
            getattr(
                response,
                "tool_calls",
                None,
            ),
        )

        return response

    # =========================================================
    # SYNC STREAMING
    # =========================================================

    def stream_with_tools(
        self,
        messages: list[BaseMessage],
    ) -> Generator[
        AIMessageChunk,
        None,
        None,
    ]:

        llm = self.get_tools_client()

        logger.info(
            "Starting tool-enabled streaming"
        )

        for chunk in llm.stream(
            messages
        ):

            if chunk is not None:
                yield chunk

        logger.info(
            "Tool-enabled streaming completed"
        )

    # =========================================================
    # ASYNC FINAL ANSWER STREAMING
    # IMPORTANT:
    # This is what workflow.stream() should use
    # AFTER MCP tool execution.
    # =========================================================

    async def astream_response(self, messages: list[BaseMessage],) -> AsyncGenerator[str, None]:
        llm = self.get_client()
        logger.info("Starting final answer streaming")
        try:
            async for chunk in llm.astream(messages):

                if chunk is None:
                    continue

                content = getattr(chunk, "content", "")

                if not content:
                    continue

                # Slow down streaming slightly
                await asyncio.sleep(0.03)

                yield str(content)

        except Exception as exc:
            logger.exception(
                "LLM streaming failed: %s",
                exc,
            )
            raise

        finally:
            logger.info(
                "Final answer streaming completed"
           )