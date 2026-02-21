"""Chat models for chat sessions and messages."""

from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, String, Text, TIMESTAMP, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class ChatSession(BaseModel):
    """Chat session entity for managing conversation contexts.
    
    Multiple sessions per user.
    Tracks session type, status, and activity timestamps.
    """
    
    __tablename__ = "chat_sessions"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Session metadata
    session_type = Column(String(50), nullable=False, default='general')
    context_data = Column(JSONB, nullable=False, default=dict)
    
    # Status
    status = Column(String(50), nullable=False, default='active')
    
    # Timestamps
    started_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    ended_at = Column(TIMESTAMP(timezone=True), nullable=True)
    last_activity_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text('CURRENT_TIMESTAMP'))
    
    # Relationships
    user = relationship("User", backref="chat_sessions")
    messages = relationship(
        "ChatMessage",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ChatMessage.created_at"
    )
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "session_type IN ('general', 'workout', 'meal', 'supplement', 'tracking')",
            name='valid_session_type'
        ),
        CheckConstraint(
            "status IN ('active', 'completed', 'abandoned')",
            name='valid_status'
        ),
        Index(
            'idx_chat_sessions_user',
            'user_id',
            'started_at',
            postgresql_ops={'started_at': 'DESC'},
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_chat_sessions_active',
            'user_id',
            'status',
            postgresql_where=(Column('status') == 'active') & (Column('deleted_at').is_(None))
        ),
    )


class ChatMessage(BaseModel):
    """Chat message entity for storing individual messages within a session.
    
    Multiple messages per session.
    Stores message content, role, and optional agent metadata.
    """
    
    __tablename__ = "chat_messages"
    
    # Foreign key to session
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("chat_sessions.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Message content
    role = Column(String(50), nullable=False)
    content = Column(Text, nullable=False)
    
    # Metadata
    agent_type = Column(String(50), nullable=True)
    message_metadata = Column('metadata', JSONB, nullable=False, default=dict)
    
    # Relationships
    session = relationship("ChatSession", back_populates="messages")
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "role IN ('user', 'assistant', 'system')",
            name='valid_role'
        ),
        CheckConstraint(
            "agent_type IS NULL OR "
            "agent_type IN ('workout_planning', 'diet_planning', 'supplement_guidance', "
            "'tracking_adjustment', 'scheduling_reminder', 'conversational')",
            name='valid_agent_type'
        ),
        Index(
            'idx_chat_messages_session',
            'session_id',
            'created_at',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
