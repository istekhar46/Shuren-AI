"""User model for authentication and identity management."""

from sqlalchemy import Boolean, Column, Index, String, UniqueConstraint
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class User(BaseModel):
    """User entity for authentication and profile management.
    
    Supports both email/password and OAuth authentication.
    Each user has one onboarding state and one profile.
    """
    
    __tablename__ = "users"
    
    # Basic user information
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=True)  # Nullable for OAuth users
    full_name = Column(String(255), nullable=False)
    
    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', NULL for email/password
    oauth_provider_user_id = Column(String(255), nullable=True)
    
    # Account status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    onboarding_state = relationship(
        "OnboardingState",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    profile = relationship(
        "UserProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint(
            'oauth_provider',
            'oauth_provider_user_id',
            name='unique_oauth_user'
        ),
        Index('idx_users_email', 'email', postgresql_where=(Column('deleted_at').is_(None))),
        Index(
            'idx_users_oauth',
            'oauth_provider',
            'oauth_provider_user_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
