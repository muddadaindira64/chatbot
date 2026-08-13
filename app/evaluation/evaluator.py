import json
import logging
from typing import Dict, Any

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.evaluation.prompts import get_evaluation_prompt

logger = logging.getLogger(__name__)


class ResponseEvaluator:
    """
    LLM-based response evaluator.
    
    Evaluates AI responses for quality, correctness, and relevance.
    """
    
    def __init__(self):
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
                temperature=0.1,  # Low temperature for consistent evaluation
                max_tokens=500
            )
        return self._client
    
    async def evaluate(self, question: str, answer: str) -> Dict[str, Any]:
        """
        Evaluate AI response quality.
        
        Args:
            question: User's question
            answer: AI's answer
            
        Returns:
            Dictionary with evaluation results
            Example: {
                "score": 0.9,
                "correctness": "good",
                "relevance": "good",
                "reason": "Answer is correct and relevant"
            }
        """
        try:
            # Check if API key is configured
            if not settings.openrouter_api_key:
                logger.warning("OpenRouter API key not configured, skipping evaluation")
                return {
                    "score": 0.0,
                    "correctness": "bad",
                    "relevance": "bad",
                    "reason": "Evaluation skipped - API key not configured"
                }
            
            # Get LLM client
            llm = self._get_client()
            
            # Get formatted prompt
            prompt = get_evaluation_prompt(question, answer)
            
            # Create messages
            messages = [
                SystemMessage(content=prompt),
                HumanMessage(content=f"Evaluate this response:\n\nQuestion: {question}\n\nAnswer: {answer}")
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
            required_fields = ["score", "correctness", "relevance", "reason"]
            for field in required_fields:
                if field not in result:
                    logger.warning("Invalid evaluation response: missing %s field", field)
                    return {
                        "score": 0.0,
                        "correctness": "bad",
                        "relevance": "bad",
                        "reason": f"Invalid evaluation response - missing {field}"
                    }
            
            # Validate score range
            score = float(result["score"])
            if not 0.0 <= score <= 1.0:
                logger.warning("Invalid score value: %s, clamping to 0.0-1.0", score)
                score = max(0.0, min(1.0, score))
                result["score"] = score
            
            # Validate correctness and relevance
            if result["correctness"] not in ["good", "bad"]:
                result["correctness"] = "bad"
            if result["relevance"] not in ["good", "bad"]:
                result["relevance"] = "bad"
            
            logger.info(
                "Response evaluated: score=%.2f, correctness=%s, relevance=%s",
                result["score"],
                result["correctness"],
                result["relevance"]
            )
            
            return result
            
        except json.JSONDecodeError as e:
            logger.error("Failed to parse evaluation response: %s", e)
            return {
                "score": 0.0,
                "correctness": "bad",
                "relevance": "bad",
                "reason": f"Failed to parse evaluation: {str(e)}"
            }
        
        except Exception as e:
            logger.exception("Error during response evaluation")
            return {
                "score": 0.0,
                "correctness": "bad",
                "relevance": "bad",
                "reason": f"Evaluation error: {str(e)}"
            }


# Singleton instance
_evaluator = None


def get_evaluator() -> ResponseEvaluator:
    """Get singleton evaluator instance."""
    global _evaluator
    if _evaluator is None:
        _evaluator = ResponseEvaluator()
    return _evaluator


async def evaluate_response(question: str, answer: str) -> Dict[str, Any]:
    """
    Convenience function to evaluate a response.
    
    Args:
        question: User's question
        answer: AI's answer
        
    Returns:
        Evaluation result dictionary
    """
    evaluator = get_evaluator()
    return await evaluator.evaluate(question, answer)