"""Workout models for workout plans, days, exercises, and exercise library."""

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, Numeric, String, Text, TIMESTAMP, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class WorkoutPlan(BaseModel):
    """Workout plan entity defining user's complete weekly workout structure.
    
    One per user.
    Contains weekly workout structure with duration and frequency.
    Can be locked to prevent accidental modifications.
    """
    
    __tablename__ = "workout_plans"
    
    # Foreign key to user
    user_id = Column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Plan metadata
    plan_name = Column(String(255), nullable=False)
    plan_description = Column(Text, nullable=True)
    duration_weeks = Column(Integer, nullable=False)
    days_per_week = Column(Integer, nullable=False)
    
    # Plan rationale
    plan_rationale = Column(Text, nullable=True)
    
    # Lock status
    is_locked = Column(Boolean, default=True, nullable=False)
    locked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="workout_plan")
    workout_days = relationship(
        "WorkoutDay",
        back_populates="workout_plan",
        cascade="all, delete-orphan",
        order_by="WorkoutDay.day_number"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('user_id', name='unique_user_workout_plan'),
        CheckConstraint(
            'duration_weeks >= 1 AND duration_weeks <= 52',
            name='valid_duration'
        ),
        CheckConstraint(
            'days_per_week >= 1 AND days_per_week <= 7',
            name='valid_days_per_week'
        ),
        Index(
            'idx_workout_plans_user_id',
            'user_id',
            unique=True,
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_workout_plans_updated',
            'updated_at',
            postgresql_ops={'updated_at': 'DESC'},
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class WorkoutDay(BaseModel):
    """Workout day entity defining a single day's workout within a plan.
    
    Multiple days per workout plan (typically 3-7).
    Contains muscle group focus and exercise list.
    """
    
    __tablename__ = "workout_days"
    
    # Foreign key to workout plan
    workout_plan_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workout_plans.id", ondelete="CASCADE"),
        nullable=False
    )
    
    # Day identification
    day_number = Column(Integer, nullable=False)
    day_name = Column(String(255), nullable=False)
    
    # Focus areas
    muscle_groups = Column(ARRAY(Text), nullable=False)
    workout_type = Column(String(50), nullable=False)
    
    # Metadata
    description = Column(Text, nullable=True)
    estimated_duration_minutes = Column(Integer, nullable=True)
    
    # Relationships
    workout_plan = relationship("WorkoutPlan", back_populates="workout_days")
    exercises = relationship(
        "WorkoutExercise",
        back_populates="workout_day",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.exercise_order"
    )
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('workout_plan_id', 'day_number', name='unique_plan_day'),
        CheckConstraint(
            'day_number >= 1 AND day_number <= 7',
            name='valid_day_number'
        ),
        CheckConstraint(
            "workout_type IN ('strength', 'cardio', 'hiit', 'active_recovery', 'rest')",
            name='valid_workout_type'
        ),
        Index(
            'idx_workout_days_plan',
            'workout_plan_id',
            'day_number',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class WorkoutExercise(BaseModel):
    """Workout exercise entity defining a specific exercise within a workout day.
    
    Multiple exercises per workout day.
    References exercise library for exercise details.
    Contains sets, reps, weight, and rest period information.
    """
    
    __tablename__ = "workout_exercises"
    
    # Foreign keys
    workout_day_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workout_days.id", ondelete="CASCADE"),
        nullable=False
    )
    exercise_library_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exercise_library.id"),
        nullable=False
    )
    
    # Exercise order
    exercise_order = Column(Integer, nullable=False)
    
    # Sets and reps
    sets = Column(Integer, nullable=False)
    reps_min = Column(Integer, nullable=True)
    reps_max = Column(Integer, nullable=True)
    reps_target = Column(Integer, nullable=True)
    
    # Weight and progression
    weight_kg = Column(Numeric(6, 2), nullable=True)
    weight_progression_type = Column(String(50), nullable=True)
    
    # Rest periods
    rest_seconds = Column(Integer, nullable=False, default=60)
    
    # Notes
    notes = Column(Text, nullable=True)
    
    # Relationships
    workout_day = relationship("WorkoutDay", back_populates="exercises")
    exercise_library = relationship("ExerciseLibrary", backref="workout_exercises")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('workout_day_id', 'exercise_order', name='unique_day_exercise_order'),
        CheckConstraint(
            'sets >= 1 AND sets <= 20',
            name='valid_sets'
        ),
        CheckConstraint(
            '(reps_target IS NOT NULL AND reps_target >= 1 AND reps_target <= 100) OR '
            '(reps_min IS NOT NULL AND reps_max IS NOT NULL AND reps_min <= reps_max)',
            name='valid_reps'
        ),
        CheckConstraint(
            'rest_seconds >= 0 AND rest_seconds <= 600',
            name='valid_rest'
        ),
        CheckConstraint(
            "weight_progression_type IS NULL OR "
            "weight_progression_type IN ('linear', 'percentage', 'rpe_based', 'none')",
            name='valid_progression'
        ),
        Index(
            'idx_workout_exercises_day',
            'workout_day_id',
            'exercise_order',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_workout_exercises_library',
            'exercise_library_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class ExerciseLibrary(BaseModel):
    """Exercise library entity containing reference data for all available exercises.
    
    Static reference table seeded with common exercises.
    Contains exercise details, instructions, and media URLs.
    """
    
    __tablename__ = "exercise_library"
    
    # Exercise identification
    exercise_name = Column(String(255), nullable=False, unique=True)
    exercise_slug = Column(String(255), nullable=False, unique=True)
    
    # Classification
    exercise_type = Column(String(50), nullable=False)
    primary_muscle_group = Column(String(100), nullable=False)
    secondary_muscle_groups = Column(ARRAY(Text), nullable=True)
    
    # Equipment
    equipment_required = Column(ARRAY(Text), nullable=False, default=list)
    
    # Difficulty
    difficulty_level = Column(String(50), nullable=False)
    
    # Instructions
    description = Column(Text, nullable=False)
    instructions = Column(Text, nullable=False)
    
    # Media
    gif_url = Column(Text, nullable=True)
    video_url = Column(Text, nullable=True)
    
    # Metadata
    is_compound = Column(Boolean, default=False, nullable=False)
    is_unilateral = Column(Boolean, default=False, nullable=False)
    
    # Table constraints
    __table_args__ = (
        CheckConstraint(
            "exercise_type IN ('strength', 'cardio', 'flexibility', 'plyometric', 'olympic')",
            name='valid_exercise_type'
        ),
        CheckConstraint(
            "difficulty_level IN ('beginner', 'intermediate', 'advanced')",
            name='valid_difficulty'
        ),
        Index(
            'idx_exercise_library_type',
            'exercise_type',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_exercise_library_muscle',
            'primary_muscle_group',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_exercise_library_difficulty',
            'difficulty_level',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
        Index(
            'idx_exercise_library_equipment',
            'equipment_required',
            postgresql_using='gin',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
