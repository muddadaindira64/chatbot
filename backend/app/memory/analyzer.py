import json
import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.memory.prompts import get_analyzer_prompt

logger = logging.getLogger(__name__)


class PersonalInfoAnalyzer:
    """
    LLM-based personal information analyzer.

    Analyzes user messages to determine if they contain personal information
    and extracts it for storage in user_memory table.
    """

    def __init__(self):
        self.prompt = get_analyzer_prompt()
        self._client = None

    def _get_client(self) -> ChatOpenAI:
        """Get or create LLM client."""
        if self._client is None:
            if not settings.openrouter_api_key:
                raise ValueError("OpenRouter API key not configured")

            self._client = ChatOpenAI(
                model="openai/gpt-4o-mini",
                api_key=settings.openrouter_api_key,
                base_url=settings.openrouter_base_url,
                temperature=0.1,  # Low temperature for consistent extraction
                max_tokens=256,   # Prevent OpenRouter 402 errors due to implicit 16k max_tokens
            )
        return self._client

    async def analyze(self, message: str) -> Dict[str, Any]:
        """
        Analyze user message for personal information.

        Args:
            message: User message to analyze

        Returns:
            Dictionary with is_personal flag and extracted data
            Example: {
                "is_personal": true,
                "data": {
                    "name": "Indira",
                    "skills": ["Python", "Django"]
                }
            }
        """
        try:
            if not message or not message.strip():
                return {"is_personal": False, "data": {}}

            if not settings.openrouter_api_key:
                logger.warning("OpenRouter API key not configured, skipping analysis")
                return {"is_personal": False, "data": {}}

            # Get LLM client
            llm = self._get_client()

            # Create messages
            messages = [
                SystemMessage(content=self.prompt),
                HumanMessage(content=message)
            ]

            # Invoke LLM
            response = llm.invoke(messages)
            content = response.content.strip()

            # Parse JSON from response
            # Handle markdown code blocks if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Parse JSON
            result = json.loads(content)

            # Validate structure
            if "is_personal" not in result:
                logger.warning("Invalid analyzer response: missing is_personal field")
                return {"is_personal": False, "data": {}}

            # Ensure data field exists
            if "data" not in result:
                result["data"] = {}

            # Log result
            if result["is_personal"]:
                logger.info(
                    "Personal information detected: %s",
                    list(result["data"].keys())
                )
            else:
                logger.debug("No personal information detected")

            return result

        except json.JSONDecodeError as e:
            logger.error("Failed to parse analyzer response: %s", e)
            return {"is_personal": False, "data": {}}

        except Exception as e:
            logger.exception("Error during personal information analysis")
            return {"is_personal": False, "data": {}}


# Singleton instance
_analyzer = None


def get_analyzer() -> PersonalInfoAnalyzer:
    """Get singleton analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = PersonalInfoAnalyzer()
    return _analyzer


async def analyze_personal_information(message: str) -> Dict[str, Any]:
    """
    Convenience function to analyze personal information.

    Args:
        message: User message to analyze

    Returns:
        Analysis result dictionary
    """
    analyzer = get_analyzer()
    return await analyzer.analyze(message)
