"""Onboarding state model for tracking user onboarding progress."""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class OnboardingState(BaseModel):
    """Onboarding state entity tracking user progress through onboarding flow.
    
    Tracks the current step (0-9) and stores step data in JSONB format.
    Each user has exactly one onboarding state.
    
    The agent_history field tracks which agents handled each state transition
    for debugging and analytics purposes.
    
    New agent foundation fields:
    - current_agent: Identifies which agent is currently handling the user
    - agent_context: JSONB data structure containing information collected by previous agents
    - conversation_history: JSONB array storing chat messages between user and agents
    """
    
    __tablename__ = "onboarding_states"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Onboarding progress (4-step flow)
    current_step = Column(Integer, default=1, nullable=False)
    is_complete = Column(Boolean, default=False, nullable=False)
    
    # Step completion tracking for 4-step flow
    step_1_complete = Column(Boolean, default=False, nullable=False)
    step_2_complete = Column(Boolean, default=False, nullable=False)
    step_3_complete = Column(Boolean, default=False, nullable=False)
    step_4_complete = Column(Boolean, default=False, nullable=False)
    
    # Agent routing history - tracks which agents handled each state
    agent_history = Column(JSONB, default=list, nullable=False)
    
    # Agent foundation fields
    current_agent = Column(String(50), nullable=True)
    agent_context = Column(JSONB, default=dict, nullable=False)
    conversation_history = Column(JSONB, default=list, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="onboarding_state")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_onboarding'),
        Index(
            'idx_onboarding_user',
            'user_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
