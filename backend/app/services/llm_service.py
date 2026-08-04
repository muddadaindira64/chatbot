import logging
from collections.abc import Generator

from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.tools.registry import AVAILABLE_TOOLS


logger = logging.getLogger(__name__)


class LLMService:

    def __init__(self) -> None:

        self.api_key = settings.openrouter_api_key
        self.model = "openai/gpt-4o-mini"
        self.base_url = "https://openrouter.ai/api/v1"

        self.client: BaseChatModel | None = None



    def get_client(self) -> BaseChatModel:


        if self.client is None:

            if not self.api_key:
                raise ValueError(
                    "OpenRouter API key is not configured."
                )


            llm = ChatOpenAI(
                model=self.model,
                api_key=self.api_key,
                base_url=self.base_url
            )


            self.client = llm.bind_tools(
                AVAILABLE_TOOLS,
                tool_choice="auto"
            )


        return self.client



    def invoke(self, messages):

        try:

            llm = self.get_client()

            response = llm.invoke(
                messages
            )
            print("MODEL RESPONSE:")
            print(response.content)

            if response.tool_calls:
                for tool in response.tool_calls:
                    print("\n🔧 Tool Used:")
                    print("Name:", tool["name"])
                    print("Args:", tool["args"])


            if getattr(response, "tool_calls", None):

                print("\n🔧 TOOL CALL DETECTED")

                for tool in response.tool_calls:

                    print(
                        "Tool Name:",
                        tool["name"]
                    )

                    print(
                        "Arguments:",
                        tool["args"]
                    )


                return response



            content = response.content


            if not content or not isinstance(content, str):

                raise ValueError(
                    "OpenRouter returned empty response"
                )


            return response


        except Exception as exc:

            logger.exception(
                "LangChain OpenRouter invocation failed"
            )

            raise exc




    def stream(
        self,
        messages
    ) -> Generator[str, None, None]:


        try:

            llm = self.get_client()


            for chunk in llm.stream(messages):

                content = getattr(
                    chunk,
                    "content",
                    None
                )


                if isinstance(content, str) and content.strip():

                    yield content



        except Exception as exc:

            logger.exception(
                "LangChain OpenRouter streaming failed"
            )

            raise exc