"""Conversation message model for text chat API."""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class ConversationMessage(BaseModel):
    """Conversation message entity for storing chat interactions.
    
    Stores all user and assistant messages in a flat structure.
    All messages for a user form one continuous conversation.
    """
    
    __tablename__ = "conversation_messages"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Message content
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    # Agent metadata (nullable for user messages)
    agent_type = Column(String(50), nullable=True)
    
    # Relationships
    user = relationship("User", backref="conversation_messages")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant')",
            name='valid_conversation_role'
        ),
        Index(
            'idx_conversation_user_created',
            'user_id',
            'created_at',
            postgresql_ops={'created_at': 'DESC'}
        ),
    )
