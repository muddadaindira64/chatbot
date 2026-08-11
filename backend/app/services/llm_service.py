import logging
from collections.abc import Generator
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessageChunk, BaseMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.tools.registry import AVAILABLE_TOOLS


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self) -> None:
        self.api_key = settings.openrouter_api_key
        self.model = settings.openrouter_model
        self.base_url = settings.openrouter_base_url

        self.client: BaseChatModel | None = None
        self.tools_client: BaseChatModel | None = None


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
                temperature=0.1,
                max_tokens=250,
                timeout=180,
            )

        return self.client


    def get_tools_client(self) -> BaseChatModel:

        if self.tools_client is None:

            self.tools_client = (
                self.get_client()
                .bind_tools(
                    AVAILABLE_TOOLS,
                )
            )

            logger.info(
                "Tools bound: %s",
                [
                    tool.name
                    for tool in AVAILABLE_TOOLS
                ]
            )

        return self.tools_client



    async def ainvoke_with_tools(
        self,
        messages:list[BaseMessage]
    ):

        llm = self.get_tools_client()

        logger.info(
            "Calling LLM with tools"
        )
        print("MODEL:", self.model)
        print("MAX TOKENS:", self.client.max_tokens)
        print("MESSAGE COUNT:", len(messages))
        response = await llm.ainvoke(
            messages
        )

        logger.info(
            "AI tool calls: %s",
            getattr(response, "tool_calls", None)
        )

        return response

    def invoke_with_tools(
        self,
        messages:list[BaseMessage]
    ):

        llm = self.get_tools_client()

        logger.info(
            "Calling LLM with tools"
        )

        response = llm.invoke(
            messages
        )

        logger.info(
            "AI tool calls: %s",
            getattr(response, "tool_calls", None)
        )

        return response



    def stream_with_tools(
        self,
        messages:list[BaseMessage]
    ) -> Generator[AIMessageChunk,None,None]:

        llm = self.get_tools_client()

        for chunk in llm.stream(messages):

            yield chunk