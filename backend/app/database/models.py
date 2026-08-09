from datetime import datetime

from sqlalchemy import (
    ForeignKey,
    String,
    Text,
    JSON,
    UniqueConstraint
)

from sqlalchemy.orm import (
    Mapped,
    mapped_column,
    relationship
)

from app.database.database import Base


# =========================
# USER TABLE
# =========================

class User(Base):

    __tablename__ = "users"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    username: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False
    )


    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False
    )


    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    # User has many conversations
    conversations: Mapped[list["Conversation"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )


    # User has one user memory (legacy profile-style memory)
    user_memory: Mapped["UserMemory"] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False
    )

    # User has many personal memories
    personal_memories: Mapped[list["PersonalMemory"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )



# =========================
# CONVERSATION / THREAD TABLE
# =========================

class Conversation(Base):

    __tablename__ = "conversations"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )


    # Chat title
    title: Mapped[str] = mapped_column(
        String(200),
        default="New Chat"
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    # relation with user
    user: Mapped["User"] = relationship(
        back_populates="conversations"
    )


    # one conversation has many messages
    messages: Mapped[list["Message"]] = relationship(
        back_populates="conversation",
        cascade="all, delete-orphan"
    )



# =========================
# MESSAGE TABLE
# =========================

class Message(Base):

    __tablename__ = "messages"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    # IMPORTANT
    # Message belongs to one conversation
    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False
    )


    role: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    content: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    conversation: Mapped["Conversation"] = relationship(
        back_populates="messages"
    )


# =========================
# USER MEMORY TABLE
# =========================

class UserMemory(Base):

    __tablename__ = "user_memory"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        nullable=False
    )


    name: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )


    role: Mapped[str] = mapped_column(
        String(100),
        nullable=True
    )


    company: Mapped[str] = mapped_column(
        String(200),
        nullable=True
    )


    skills: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list
    )


    preferences: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
        default=dict
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )


    # relationship with user
    user: Mapped["User"] = relationship(
        back_populates="user_memory"
    )


# =========================
# PERSONAL MEMORY TABLE
# =========================

class PersonalMemory(Base):

    __tablename__ = "personal_memories"
    __table_args__ = (
        UniqueConstraint("user_id", "key", name="uq_user_personal_memory_key"),
    )

    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    key: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True
    )

    value: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )

    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow,
        onupdate=datetime.utcnow
    )

    user: Mapped["User"] = relationship(
        back_populates="personal_memories"
    )


# =========================
# FEEDBACK TABLE
# =========================

class Feedback(Base):

    __tablename__ = "feedback"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )


    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False
    )


    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        nullable=False
    )


    rating: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    comment: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    # relationships
    user: Mapped["User"] = relationship()
    conversation: Mapped["Conversation"] = relationship()
    message: Mapped["Message"] = relationship()


# =========================
# EVALUATION TABLE
# =========================

class Evaluation(Base):

    __tablename__ = "evaluations"


    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True
    )


    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False
    )


    conversation_id: Mapped[int] = mapped_column(
        ForeignKey("conversations.id"),
        nullable=False
    )


    message_id: Mapped[int] = mapped_column(
        ForeignKey("messages.id"),
        nullable=False
    )


    question: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )


    answer: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )


    score: Mapped[float] = mapped_column(
        nullable=False
    )


    correctness: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    relevance: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )


    reason: Mapped[str] = mapped_column(
        Text,
        nullable=True
    )


    created_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow
    )


    # relationships
    user: Mapped["User"] = relationship()
    conversation: Mapped["Conversation"] = relationship()
    message: Mapped["Message"] = relationship()
