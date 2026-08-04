from datetime import datetime

from sqlalchemy.orm import Session

from app.database.models import Conversation, Message, User


class ConversationService:
    def __init__(self, db: Session) -> None:
        self.db = db

    def create_conversation(self, user_id: int, title: str) -> Conversation:
        conversation = Conversation(user_id=user_id, title=title, created_at=datetime.utcnow())
        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_user_conversations(self, user_id: int) -> list[Conversation]:
        return self.db.query(Conversation).filter(Conversation.user_id == user_id).order_by(Conversation.created_at.desc()).all()

    def get_conversation_messages(self, conversation_id: int, user_id: int) -> list[Message]:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
        if conversation is None:
            return []
        return self.db.query(Message).filter(Message.conversation_id == conversation_id).order_by(Message.created_at.asc()).all()

    def save_message(self, conversation_id: int, role: str, content: str) -> Message:
        message = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            created_at=datetime.utcnow(),
        )
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def delete_conversation(self, conversation_id: int, user_id: int) -> bool:
        conversation = self.db.query(Conversation).filter(Conversation.id == conversation_id, Conversation.user_id == user_id).first()
        if conversation is None:
            return False
        self.db.delete(conversation)
        self.db.commit()
        return True
