import logging
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.models import Evaluation, Message, Conversation
from app.evaluation.evaluator import evaluate_response

logger = logging.getLogger(__name__)


async def save_evaluation(
    db: AsyncSession,
    user_id: int,
    conversation_id: int,
    message_id: int,
    question: str,
    answer: str
) -> Evaluation:
    """
    Evaluate AI response and save to database.
    
    Args:
        db: Database session
        user_id: User ID
        conversation_id: Conversation ID
        message_id: Message ID (assistant message)
        question: User's question
        answer: AI's answer
        
    Returns:
        Evaluation object
    """
    try:
        # Get evaluation from LLM
        evaluation_data = await evaluate_response(question, answer)
        
        # Create evaluation record
        evaluation = Evaluation(
            user_id=user_id,
            conversation_id=conversation_id,
            message_id=message_id,
            question=question,
            answer=answer,
            score=evaluation_data.get("score", 0.0),
            correctness=evaluation_data.get("correctness", "bad"),
            relevance=evaluation_data.get("relevance", "bad"),
            reason=evaluation_data.get("reason", "")
        )
        
        db.add(evaluation)
        await db.commit()
        await db.refresh(evaluation)
        
        logger.info(
            "Evaluation saved: message_id=%s, score=%.2f",
            message_id,
            evaluation.score
        )
        
        return evaluation
    
    except Exception as e:
        await db.rollback()
        logger.error("Failed to save evaluation: %s", str(e))
        raise


async def get_evaluation_for_message(
    db: AsyncSession,
    message_id: int
) -> Evaluation | None:
    """
    Get evaluation for a specific message.
    
    Args:
        db: Database session
        message_id: Message ID
        
    Returns:
        Evaluation object or None
    """
    result = await db.execute(
        select(Evaluation).where(Evaluation.message_id == message_id)
    )
    return result.scalar_one_or_none()