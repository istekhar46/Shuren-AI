"""Workout log model for tracking workout sets logged via voice interactions."""

from sqlalchemy import Column, DateTime, Float, ForeignKey, Index, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class WorkoutLog(BaseModel):
    """Workout log entity for tracking individual workout sets.
    
    Stores workout set logs from voice interactions.
    Each log entry records exercise name, reps, weight, and timestamp.
    """
    
    __tablename__ = "workout_logs"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Exercise details
    exercise = Column(String(255), nullable=False)
    reps = Column(Integer, nullable=False)
    weight_kg = Column(Float, nullable=False)
    
    # Timestamp when the set was logged
    logged_at = Column(DateTime(timezone=True), nullable=False)
    
    # Relationships
    user = relationship("User", backref="workout_logs")
    
    # Table constraints
    __table_args__ = (
        Index(
            'idx_workout_logs_user_id',
            'user_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_workout_logs_logged_at',
            'logged_at',
            postgresql_ops={'logged_at': 'DESC'},
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_workout_logs_user_logged',
            'user_id',
            'logged_at',
            postgresql_ops={'logged_at': 'DESC'},
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
