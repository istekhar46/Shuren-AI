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
    
    @property
    def onboarding_completed(self) -> bool:
        """Check if user has completed onboarding.
        
        Returns:
            True if onboarding_state exists and is_complete is True, False otherwise
        
        Note:
            This property safely checks if the onboarding_state relationship is loaded
            before accessing it to avoid triggering lazy loads in async contexts.
        """
        from sqlalchemy.inspection import inspect as sqlalchemy_inspect
        from sqlalchemy.orm.base import NO_VALUE
        
        # Check if the onboarding_state relationship is loaded
        state = sqlalchemy_inspect(self)
        
        # If the relationship is not loaded, return False
        if 'onboarding_state' not in state.attrs or state.attrs.onboarding_state.loaded_value is NO_VALUE:
            return False
        
        # If loaded, safely access the value
        onboarding_state = state.attrs.onboarding_state.loaded_value
        
        # If None or not complete, return False
        if onboarding_state is None:
            return False
        
        return onboarding_state.is_complete
    
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
