"""Profile and preferences Pydantic schemas"""

from datetime import time
from typing import Any, List, Optional

from pydantic import BaseModel, Field, field_validator


class FitnessGoalSchema(BaseModel):
    """Schema for fitness goals"""
    goal_type: str = Field(..., description="Goal type: fat_loss, muscle_gain, general_fitness")
    target_weight_kg: Optional[float] = Field(None, description="Target weight in kilograms")
    target_body_fat_percentage: Optional[float] = Field(None, description="Target body fat percentage")
    priority: int = Field(1, description="Goal priority")
    
    class Config:
        from_attributes = True


class PhysicalConstraintSchema(BaseModel):
    """Schema for physical constraints"""
    constraint_type: str = Field(..., description="Constraint type: equipment, injury, limitation")
    description: str = Field(..., description="Detailed description of the constraint")
    severity: Optional[str] = Field(None, description="Severity: low, medium, high")
    
    class Config:
        from_attributes = True


class DietaryPreferenceSchema(BaseModel):
    """Schema for dietary preferences"""
    diet_type: str = Field(..., description="Diet type: omnivore, vegetarian, vegan, pescatarian, keto, paleo")
    allergies: List[str] = Field(default_factory=list, description="List of food allergies")
    intolerances: List[str] = Field(default_factory=list, description="List of food intolerances")
    dislikes: List[str] = Field(default_factory=list, description="List of disliked foods")
    
    class Config:
        from_attributes = True


class MealPlanSchema(BaseModel):
    """Schema for meal plan with macro validation"""
    daily_calorie_target: int = Field(..., gt=0, description="Daily calorie target")
    protein_percentage: float = Field(..., ge=0, le=100, description="Protein percentage of total calories")
    carbs_percentage: float = Field(..., ge=0, le=100, description="Carbs percentage of total calories")
    fats_percentage: float = Field(..., ge=0, le=100, description="Fats percentage of total calories")
    
    @field_validator('fats_percentage')
    @classmethod
    def validate_macro_sum(cls, v: float, info) -> float:
        """Validate that macronutrient percentages sum to 100"""
        if info.data:
            protein = info.data.get('protein_percentage', 0)
            carbs = info.data.get('carbs_percentage', 0)
            total = protein + carbs + v
            if abs(total - 100.0) > 0.01:  # Allow small floating point errors
                raise ValueError(f'Macronutrient percentages must sum to 100, got {total}')
        return v
    
    class Config:
        from_attributes = True


class MealScheduleSchema(BaseModel):
    """Schema for meal schedule"""
    meal_name: str = Field(..., description="Meal name: breakfast, lunch, dinner, snack_1, etc.")
    scheduled_time: time = Field(..., description="Scheduled time for the meal")
    enable_notifications: bool = Field(True, description="Enable notifications for this meal")
    
    class Config:
        from_attributes = True


class WorkoutScheduleSchema(BaseModel):
    """Schema for workout schedule"""
    day_of_week: int = Field(..., ge=0, le=6, description="Day of week: 0=Monday, 6=Sunday")
    scheduled_time: time = Field(..., description="Scheduled time for the workout")
    enable_notifications: bool = Field(True, description="Enable notifications for this workout")
    
    class Config:
        from_attributes = True


class HydrationPreferenceSchema(BaseModel):
    """Schema for hydration preferences"""
    daily_water_target_ml: int = Field(..., gt=0, description="Daily water intake target in milliliters")
    reminder_frequency_minutes: int = Field(60, gt=0, description="Reminder frequency in minutes")
    enable_notifications: bool = Field(True, description="Enable hydration reminders")
    
    class Config:
        from_attributes = True


class LifestyleBaselineSchema(BaseModel):
    """Schema for lifestyle baseline with range validation"""
    energy_level: int = Field(..., ge=1, le=10, description="Energy level rating (1-10)")
    stress_level: int = Field(..., ge=1, le=10, description="Stress level rating (1-10)")
    sleep_quality: int = Field(..., ge=1, le=10, description="Sleep quality rating (1-10)")
    
    class Config:
        from_attributes = True


class UserProfileResponse(BaseModel):
    """Schema for complete user profile response"""
    id: str
    user_id: str
    is_locked: bool
    fitness_level: str
    fitness_goals: List[FitnessGoalSchema]
    physical_constraints: List[PhysicalConstraintSchema]
    dietary_preferences: Optional[DietaryPreferenceSchema] = None
    meal_plan: Optional[MealPlanSchema] = None
    meal_schedules: List[MealScheduleSchema]
    workout_schedules: List[WorkoutScheduleSchema]
    hydration_preferences: Optional[HydrationPreferenceSchema] = None
    lifestyle_baseline: Optional[LifestyleBaselineSchema] = None
    
    class Config:
        from_attributes = True


class ProfileUpdateRequest(BaseModel):
    """Schema for profile update request"""
    reason: str = Field(..., min_length=1, max_length=500, description="Reason for profile modification")
    updates: dict[str, Any] = Field(..., description="Profile updates to apply")
