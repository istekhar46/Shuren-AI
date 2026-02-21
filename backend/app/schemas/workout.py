"""Workout plan and schedule Pydantic schemas"""

from datetime import datetime, time
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field


# Response Schemas

class ExerciseLibraryBase(BaseModel):
    """
    Schema for exercise library reference data.
    
    Contains all information needed to perform an exercise correctly,
    including visual guidance and difficulty level.
    """
    id: UUID = Field(..., description="Unique identifier for the exercise")
    exercise_name: str = Field(..., description="Display name of the exercise (e.g., 'Barbell Bench Press')")
    exercise_slug: str = Field(..., description="URL-friendly slug for the exercise")
    exercise_type: str = Field(..., description="Type of exercise: strength, cardio, flexibility, plyometric, olympic")
    primary_muscle_group: str = Field(..., description="Primary muscle group targeted (e.g., 'chest', 'back', 'legs')")
    secondary_muscle_groups: List[str] = Field(..., description="Secondary muscle groups engaged during the exercise")
    equipment_required: List[str] = Field(..., description="Equipment needed (e.g., ['barbell', 'bench'])")
    difficulty_level: str = Field(..., description="Difficulty level: beginner, intermediate, advanced")
    description: str = Field(..., description="Brief description of the exercise")
    instructions: str = Field(..., description="Step-by-step instructions for performing the exercise")
    gif_url: Optional[str] = Field(None, description="URL to animated GIF demonstrating proper form")
    is_compound: bool = Field(..., description="Whether this is a compound movement (multiple joints)")
    is_unilateral: bool = Field(..., description="Whether this exercise is performed one side at a time")
    
    class Config:
        from_attributes = True


class WorkoutExerciseResponse(BaseModel):
    """
    Schema for workout exercise with library details.
    
    Represents a specific exercise within a workout day, including sets, reps,
    weight, and complete exercise library information.
    """
    id: UUID = Field(..., description="Unique identifier for this workout exercise instance")
    exercise_order: int = Field(..., description="Order of this exercise in the workout (1-based)")
    sets: int = Field(..., description="Number of sets to perform (1-20)")
    reps_min: Optional[int] = Field(None, description="Minimum reps per set (for rep ranges)")
    reps_max: Optional[int] = Field(None, description="Maximum reps per set (for rep ranges)")
    reps_target: Optional[int] = Field(None, description="Target reps per set (for fixed rep schemes)")
    weight_kg: Optional[Decimal] = Field(None, description="Weight in kilograms to use")
    weight_progression_type: Optional[str] = Field(None, description="Progression strategy: linear, percentage, rpe_based, none")
    rest_seconds: int = Field(..., description="Rest period between sets in seconds (0-600)")
    notes: Optional[str] = Field(None, description="Additional notes or instructions for this exercise")
    exercise_library: ExerciseLibraryBase = Field(..., description="Complete exercise library details")
    
    class Config:
        from_attributes = True


class WorkoutDayResponse(BaseModel):
    """
    Schema for workout day with exercises.
    
    Represents a single day's workout within a weekly plan, including all
    exercises and metadata about the workout focus.
    """
    id: UUID = Field(..., description="Unique identifier for this workout day")
    day_number: int = Field(..., description="Day number in the week (1-7)")
    day_name: str = Field(..., description="Name of the workout day (e.g., 'Upper Body Push', 'Leg Day')")
    muscle_groups: List[str] = Field(..., description="Muscle groups targeted in this workout")
    workout_type: str = Field(..., description="Type of workout: strength, cardio, hiit, active_recovery, rest")
    description: Optional[str] = Field(None, description="Description of the workout focus and goals")
    estimated_duration_minutes: Optional[int] = Field(None, description="Estimated time to complete the workout (15-180 minutes)")
    exercises: List[WorkoutExerciseResponse] = Field(..., description="List of exercises in order of execution")
    
    class Config:
        from_attributes = True


class WorkoutPlanResponse(BaseModel):
    """
    Schema for complete workout plan.
    
    Represents the user's complete weekly workout structure with all days
    and exercises. This is the primary data structure for workout management.
    """
    id: UUID = Field(..., description="Unique identifier for this workout plan")
    plan_name: str = Field(..., description="Name of the workout plan (e.g., 'Beginner Full Body')")
    plan_description: Optional[str] = Field(None, description="Detailed description of the plan's approach and goals")
    duration_weeks: int = Field(..., description="Planned duration of the program in weeks (1-52)")
    days_per_week: int = Field(..., description="Number of workout days per week (1-7)")
    plan_rationale: Optional[str] = Field(None, description="AI-generated explanation of why this plan suits the user")
    is_locked: bool = Field(..., description="Whether the plan is locked (requires unlock to modify)")
    workout_days: List[WorkoutDayResponse] = Field(..., description="All workout days in the plan")
    created_at: datetime = Field(..., description="Timestamp when the plan was created")
    updated_at: datetime = Field(..., description="Timestamp of last modification")
    
    class Config:
        from_attributes = True


class WorkoutScheduleResponse(BaseModel):
    """
    Schema for workout schedule configuration.
    
    Represents when workouts are scheduled throughout the week.
    """
    id: UUID = Field(..., description="Unique identifier for this schedule entry")
    day_of_week: int = Field(..., description="Day of week (0=Monday, 6=Sunday)")
    scheduled_time: time = Field(..., description="Time of day for the workout")
    enable_notifications: bool = Field(..., description="Whether to send reminder notifications")
    
    class Config:
        from_attributes = True



# Update Schemas

class ExerciseUpdate(BaseModel):
    """
    Schema for updating workout exercise.
    
    Used when modifying exercises within a workout plan. All fields are required
    to ensure complete exercise specification.
    """
    exercise_library_id: UUID = Field(..., description="Reference to exercise in library")
    exercise_order: int = Field(..., description="Order of this exercise in the workout")
    sets: int = Field(..., ge=1, le=20, description="Number of sets (1-20)")
    reps_min: Optional[int] = Field(None, ge=1, le=100, description="Minimum reps for rep range (1-100)")
    reps_max: Optional[int] = Field(None, ge=1, le=100, description="Maximum reps for rep range (1-100)")
    reps_target: Optional[int] = Field(None, ge=1, le=100, description="Target reps for fixed scheme (1-100)")
    weight_kg: Optional[Decimal] = Field(None, ge=0, description="Weight in kilograms (must be non-negative)")
    weight_progression_type: Optional[str] = Field(None, description="Progression strategy: linear, percentage, rpe_based, none")
    rest_seconds: int = Field(default=60, ge=0, le=600, description="Rest between sets in seconds (0-600)")
    notes: Optional[str] = Field(None, description="Additional notes or instructions")
    
    class Config:
        json_schema_extra = {
            "example": {
                "exercise_library_id": "123e4567-e89b-12d3-a456-426614174000",
                "exercise_order": 1,
                "sets": 3,
                "reps_target": 10,
                "weight_kg": 60.0,
                "weight_progression_type": "linear",
                "rest_seconds": 90,
                "notes": "Focus on controlled eccentric"
            }
        }


class WorkoutDayUpdate(BaseModel):
    """
    Schema for updating workout day.
    
    Used when modifying a workout day within a plan. Requires complete
    specification of the day including all exercises.
    """
    day_number: int = Field(..., ge=1, le=7, description="Day number in the week (1-7)")
    day_name: str = Field(..., description="Name of the workout day")
    muscle_groups: List[str] = Field(..., description="Muscle groups targeted")
    workout_type: str = Field(..., description="Type: strength, cardio, hiit, active_recovery, rest")
    description: Optional[str] = Field(None, description="Description of workout focus")
    estimated_duration_minutes: Optional[int] = Field(None, ge=15, le=180, description="Estimated duration (15-180 minutes)")
    exercises: List[ExerciseUpdate] = Field(..., description="Complete list of exercises")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_number": 1,
                "day_name": "Upper Body Push",
                "muscle_groups": ["chest", "shoulders", "triceps"],
                "workout_type": "strength",
                "description": "Focus on pushing movements",
                "estimated_duration_minutes": 60,
                "exercises": []
            }
        }


class WorkoutPlanUpdate(BaseModel):
    """
    Schema for updating workout plan.
    
    All fields are optional to support partial updates. Profile must be
    unlocked before modifications are allowed.
    """
    plan_name: Optional[str] = Field(None, description="New name for the workout plan")
    plan_description: Optional[str] = Field(None, description="Updated description")
    duration_weeks: Optional[int] = Field(None, ge=1, le=52, description="New duration in weeks (1-52)")
    days_per_week: Optional[int] = Field(None, ge=1, le=7, description="New number of workout days (1-7)")
    workout_days: Optional[List[WorkoutDayUpdate]] = Field(None, description="Updated workout days")
    
    class Config:
        json_schema_extra = {
            "example": {
                "plan_name": "Advanced Strength Program",
                "duration_weeks": 16,
                "days_per_week": 5
            }
        }


class WorkoutScheduleUpdate(BaseModel):
    """
    Schema for updating workout schedule.
    
    All fields are optional to support partial updates. Profile must be
    unlocked before modifications are allowed.
    """
    day_of_week: Optional[int] = Field(None, ge=0, le=6, description="Day of week (0=Monday, 6=Sunday)")
    scheduled_time: Optional[time] = Field(None, description="Time of day for the workout")
    enable_notifications: Optional[bool] = Field(None, description="Whether to send reminder notifications")
    
    class Config:
        json_schema_extra = {
            "example": {
                "day_of_week": 1,
                "scheduled_time": "18:00:00",
                "enable_notifications": True
            }
        }
