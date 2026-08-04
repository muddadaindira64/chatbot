import logging
from collections.abc import AsyncGenerator
from typing import Any

from fastapi import HTTPException, status

from app.core.config import settings
from app.graph.workflow import ChatWorkflow
from app.prompts.chat_prompt import build_prompt

from app.memory.service import add_conversation


logger = logging.getLogger(__name__)


class AIService:

    def __init__(self) -> None:

        self.api_key = settings.openrouter_api_key
        self.workflow = ChatWorkflow()


    async def complete(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> str:


        if not self.api_key:

            logger.error(
                "OpenRouter API key is missing"
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )


        try:

            prompt = build_prompt(
                user_message=message,
                context=context,
                history=history,
            )


        except ValueError as exc:

            logger.exception(
                "Prompt generation failed"
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc



        try:

            response = self.workflow.run(prompt)


            # Save assistant response

            add_conversation(
                role="assistant",
                content=response
            )


            return response



        except Exception as exc:

            logger.exception(
                "LangGraph workflow execution failed"
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Workflow execution failed while calling OpenRouter.",
            ) from exc



    async def stream_complete(
        self,
        message: str,
        context: str | None = None,
        history: list[dict[str, Any]] | None = None,
    ) -> AsyncGenerator[str, None]:


        if not self.api_key:

            logger.error(
                "OpenRouter API key is missing"
            )

            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="OpenRouter API key is not configured.",
            )



        try:

            prompt = build_prompt(
                user_message=message,
                context=context,
                history=history,
            )


        except ValueError as exc:

            logger.exception(
                "Prompt generation failed"
            )

            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(exc),
            ) from exc




        try:

            full_response = ""


            for chunk in self.workflow.stream(prompt):


                # Send chunk to frontend

                yield chunk



                # Collect complete response

                full_response += chunk




            # Save final assistant message

            if full_response.strip():

                add_conversation(
                    role="assistant",
                    content=full_response.strip()
                )



        except Exception as exc:

            logger.exception(
                "Streaming workflow execution failed"
            )

            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail="Streaming response failed while calling OpenRouter.",
            ) from exc