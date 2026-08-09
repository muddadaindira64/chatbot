import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database.database import get_db
from app.database.models import Feedback, Message, Conversation
from app.auth.dependencies import get_current_user
from app.schemas.feedback import FeedbackCreate, FeedbackResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/feedback", tags=["feedback"])


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
async def create_feedback(
    feedback_data: FeedbackCreate,
    current_user = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit feedback for an AI message.
    
    Validates:
    - Message exists
    - Message belongs to user's conversation
    - User owns the conversation
    """
    try:
        # Get the message
        result = await db.execute(
            select(Message).where(Message.id == feedback_data.message_id)
        )
        message = result.scalar_one_or_none()
        
        if not message:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Message not found"
            )
        
        # Get the conversation
        result = await db.execute(
            select(Conversation).where(Conversation.id == message.conversation_id)
        )
        conversation = result.scalar_one_or_none()
        
        if not conversation:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Conversation not found"
            )
        
        # Verify user owns the conversation
        if conversation.user_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only provide feedback for your own conversations"
            )
        
        # Create feedback
        feedback = Feedback(
            user_id=current_user.id,
            conversation_id=conversation.id,
            message_id=message.id,
            rating=feedback_data.rating,
            comment=feedback_data.comment
        )
        
        db.add(feedback)
        await db.commit()
        await db.refresh(feedback)
        
        return {
            "message": "Feedback saved successfully",
            "feedback_id": feedback.id
        }
    
    except HTTPException:
        raise
    
    except Exception as e:
        await db.rollback()
        logger.exception("Error saving feedback")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to save feedback"
        ) from e