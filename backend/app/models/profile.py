"""User profile models for fitness configuration and versioning."""

from sqlalchemy import Boolean, Column, ForeignKey, Index, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class UserProfile(BaseModel):
    """User profile entity containing fitness configuration.
    
    Represents the single source of truth for user's fitness preferences.
    Each user has at most one active profile.
    Profile can be locked to prevent accidental modifications.
    """
    
    __tablename__ = "user_profiles"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False
    )
    
    # Profile state
    is_locked = Column(Boolean, default=False, nullable=False)
    fitness_level = Column(String(50), nullable=True)  # 'beginner', 'intermediate', 'advanced'
    
    # Relationships
    user = relationship("User", back_populates="profile")
    
    versions = relationship(
        "UserProfileVersion",
        back_populates="profile",
        cascade="all, delete-orphan",
        order_by="UserProfileVersion.version_number.desc()"
    )
    
    fitness_goals = relationship(
        "FitnessGoal",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    physical_constraints = relationship(
        "PhysicalConstraint",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    dietary_preferences = relationship(
        "DietaryPreference",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    meal_plan = relationship(
        "MealPlan",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    meal_schedules = relationship(
        "MealSchedule",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    workout_schedules = relationship(
        "WorkoutSchedule",
        back_populates="profile",
        cascade="all, delete-orphan"
    )
    
    hydration_preferences = relationship(
        "HydrationPreference",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    lifestyle_baseline = relationship(
        "LifestyleBaseline",
        back_populates="profile",
        uselist=False,
        cascade="all, delete-orphan"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_profile'),
        Index(
            'idx_profile_user',
            'user_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class UserProfileVersion(BaseModel):
    """Profile version entity for audit trail of profile changes.
    
    Immutable record of profile state at a point in time.
    Created before any profile modification.
    """
    
    __tablename__ = "user_profile_versions"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Version information
    version_number = Column(Integer, nullable=False)
    change_reason = Column(String(500), nullable=True)
    
    # Complete snapshot of profile state
    snapshot = Column(JSONB, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="versions")
    
    # Table constraints
    __table_args__ = (
        Index('idx_profile_versions', 'profile_id', 'version_number'),
    )
