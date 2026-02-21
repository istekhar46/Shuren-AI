"""Preference models for fitness goals, constraints, diet, meals, workouts, and lifestyle."""

from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Index, Integer, Numeric, String, Text, Time, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY, UUID
from sqlalchemy.orm import relationship

from app.db.base import BaseModel


class FitnessGoal(BaseModel):
    """Fitness goal entity defining user's fitness objectives.
    
    Supports multiple goals per user with priorities.
    Goals can have quantifiable targets (weight, body fat percentage).
    """
    
    __tablename__ = "fitness_goals"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Goal details
    goal_type = Column(String(50), nullable=False)  # 'fat_loss', 'muscle_gain', 'general_fitness'
    target_weight_kg = Column(Numeric(5, 2), nullable=True)
    target_body_fat_percentage = Column(Numeric(4, 2), nullable=True)
    priority = Column(Integer, default=1, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="fitness_goals")
    
    # Table constraints
    __table_args__ = (
        Index(
            'idx_fitness_goals_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class PhysicalConstraint(BaseModel):
    """Physical constraint entity for equipment, injuries, and limitations.
    
    Tracks user's physical limitations and available equipment.
    Used to tailor workout recommendations.
    """
    
    __tablename__ = "physical_constraints"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Constraint details
    constraint_type = Column(String(50), nullable=False)  # 'equipment', 'injury', 'limitation'
    description = Column(Text, nullable=False)
    severity = Column(String(20), nullable=True)  # 'low', 'medium', 'high'
    
    # Relationships
    profile = relationship("UserProfile", back_populates="physical_constraints")
    
    # Table constraints
    __table_args__ = (
        Index(
            'idx_physical_constraints_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class DietaryPreference(BaseModel):
    """Dietary preference entity for diet type and restrictions.
    
    One per user profile.
    Stores diet type, allergies, intolerances, and dislikes.
    """
    
    __tablename__ = "dietary_preferences"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Diet details
    diet_type = Column(String(50), nullable=False)  # 'omnivore', 'vegetarian', 'vegan', 'pescatarian', 'keto', 'paleo'
    allergies = Column(ARRAY(Text), default=list, nullable=False)
    intolerances = Column(ARRAY(Text), default=list, nullable=False)
    dislikes = Column(ARRAY(Text), default=list, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="dietary_preferences")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('profile_id', name='unique_profile_dietary'),
        Index(
            'idx_dietary_preferences_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class MealPlan(BaseModel):
    """Meal plan entity defining daily nutritional targets.
    
    One per user profile.
    Defines calorie target and macronutrient distribution.
    Macros must sum to 100%.
    """
    
    __tablename__ = "meal_plans"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Nutritional targets (in grams for precision and clarity)
    daily_calorie_target = Column(Integer, nullable=False)
    protein_grams = Column(Numeric(6, 2), nullable=False)
    carbs_grams = Column(Numeric(6, 2), nullable=False)
    fats_grams = Column(Numeric(6, 2), nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_plan")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('profile_id', name='unique_profile_meal_plan'),
        Index(
            'idx_meal_plans_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class MealSchedule(BaseModel):
    """Meal schedule entity for meal timing and notifications.
    
    Multiple schedules per user profile (breakfast, lunch, dinner, snacks).
    Defines when meals should occur and notification preferences.
    """
    
    __tablename__ = "meal_schedules"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Schedule details
    meal_name = Column(String(100), nullable=False)  # 'breakfast', 'lunch', 'dinner', 'snack_1', etc.
    scheduled_time = Column(Time, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="meal_schedules")
    
    # Table constraints
    __table_args__ = (
        Index(
            'idx_meal_schedules_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class WorkoutSchedule(BaseModel):
    """Workout schedule entity for workout timing and notifications.
    
    Multiple schedules per user profile (one per workout day).
    Defines workout days and times with notification preferences.
    """
    
    __tablename__ = "workout_schedules"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Schedule details
    day_of_week = Column(Integer, nullable=False)  # 0=Monday, 6=Sunday
    scheduled_time = Column(Time, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="workout_schedules")
    
    # Table constraints
    __table_args__ = (
        Index(
            'idx_workout_schedules_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class HydrationPreference(BaseModel):
    """Hydration preference entity for water intake reminders.
    
    One per user profile.
    Defines daily water target and reminder frequency.
    """
    
    __tablename__ = "hydration_preferences"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Hydration details
    daily_water_target_ml = Column(Integer, nullable=False)
    reminder_frequency_minutes = Column(Integer, default=60, nullable=False)
    enable_notifications = Column(Boolean, default=True, nullable=False)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="hydration_preferences")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('profile_id', name='unique_profile_hydration'),
        Index(
            'idx_hydration_preferences_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )


class LifestyleBaseline(BaseModel):
    """Lifestyle baseline entity for energy, stress, and sleep tracking.
    
    One per user profile.
    Tracks self-reported lifestyle metrics on 1-10 scale.
    """
    
    __tablename__ = "lifestyle_baselines"
    
    # Foreign key to profile
    profile_id = Column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id"),
        nullable=False
    )
    
    # Lifestyle metrics (1-10 scale)
    energy_level = Column(Integer, nullable=True)
    stress_level = Column(Integer, nullable=True)
    sleep_quality = Column(Integer, nullable=True)
    
    # Relationships
    profile = relationship("UserProfile", back_populates="lifestyle_baseline")
    
    # Table constraints
    __table_args__ = (
        UniqueConstraint('profile_id', name='unique_profile_lifestyle'),
        CheckConstraint('energy_level BETWEEN 1 AND 10', name='valid_energy_level'),
        CheckConstraint('stress_level BETWEEN 1 AND 10', name='valid_stress_level'),
        CheckConstraint('sleep_quality BETWEEN 1 AND 10', name='valid_sleep_quality'),
        Index(
            'idx_lifestyle_baselines_profile',
            'profile_id',
            postgresql_where=(Column('deleted_at').is_(None))
        ),
    )
