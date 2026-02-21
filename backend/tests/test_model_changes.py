"""
Test database model changes for agent context compatibility.

Tests the new plan_data JSONB column in WorkoutPlan and gram-based
macro columns in MealPlan to ensure they work with agent context data.
"""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.workout import WorkoutPlan
from app.models.preferences import MealPlan
from app.models.profile import UserProfile
from app.models.user import User


@pytest.mark.asyncio
async def test_workout_plan_with_plan_data_jsonb(db_session: AsyncSession):
    """Test that WorkoutPlan can store complete plan data as JSONB."""
    # Create a test user
    user = User(
        email="test_workout@example.com",
        hashed_password="test_hash",
        full_name="Test Workout User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Sample plan data from agent context (matches WorkoutPlanGenerator output)
    plan_data = {
        "frequency": 4,
        "location": "gym",
        "duration_minutes": 60,
        "equipment": ["barbell", "dumbbells", "bench"],
        "training_split": "upper_lower",
        "exercises": [
            {
                "day": 1,
                "name": "Barbell Squat",
                "sets": 4,
                "reps": "8-10",
                "rest_seconds": 120,
                "notes": "Focus on depth"
            },
            {
                "day": 1,
                "name": "Romanian Deadlift",
                "sets": 3,
                "reps": "10-12",
                "rest_seconds": 90,
                "notes": "Control the eccentric"
            }
        ],
        "progression_strategy": "linear_progression",
        "rationale": "Upper/lower split for intermediate lifter focusing on muscle gain"
    }
    
    # Create WorkoutPlan with plan_data
    workout_plan = WorkoutPlan(
        user_id=user.id,
        plan_name="4-Day Upper/Lower Split",
        plan_description="Intermediate muscle gain program",
        duration_weeks=12,
        days_per_week=4,
        plan_rationale="Optimal frequency for muscle gain at intermediate level",
        plan_data=plan_data,  # Store complete agent context data
        is_locked=True
    )
    
    db_session.add(workout_plan)
    await db_session.commit()
    await db_session.refresh(workout_plan)
    
    # Verify plan_data is stored correctly
    assert workout_plan.plan_data is not None
    assert workout_plan.plan_data["frequency"] == 4
    assert workout_plan.plan_data["location"] == "gym"
    assert workout_plan.plan_data["training_split"] == "upper_lower"
    assert len(workout_plan.plan_data["exercises"]) == 2
    assert workout_plan.plan_data["exercises"][0]["name"] == "Barbell Squat"
    
    # Verify we can query and retrieve the plan
    stmt = select(WorkoutPlan).where(WorkoutPlan.user_id == user.id)
    result = await db_session.execute(stmt)
    retrieved_plan = result.scalars().first()
    
    assert retrieved_plan is not None
    assert retrieved_plan.plan_data["frequency"] == 4
    assert retrieved_plan.plan_data["progression_strategy"] == "linear_progression"


@pytest.mark.asyncio
async def test_meal_plan_with_gram_based_macros(db_session: AsyncSession):
    """Test that MealPlan stores macros in grams (not percentages)."""
    # Create a test user and profile
    user = User(
        email="test_meal@example.com",
        hashed_password="test_hash",
        full_name="Test Meal User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    profile = UserProfile(
        user_id=user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Sample meal plan data from agent context (matches MealPlanGenerator output)
    # For muscle gain: 2500 calories, 188g protein, 281g carbs, 69g fats
    # Calculation: (188*4) + (281*4) + (69*9) = 752 + 1124 + 621 = 2497 ≈ 2500
    meal_plan = MealPlan(
        profile_id=profile.id,
        daily_calorie_target=2500,
        protein_grams=188.0,  # Gram-based (not percentage)
        carbs_grams=281.0,    # Gram-based (not percentage)
        fats_grams=69.0       # Gram-based (not percentage)
    )
    
    db_session.add(meal_plan)
    await db_session.commit()
    await db_session.refresh(meal_plan)
    
    # Verify gram-based macros are stored correctly
    assert meal_plan.daily_calorie_target == 2500
    assert meal_plan.protein_grams == 188.0
    assert meal_plan.carbs_grams == 281.0
    assert meal_plan.fats_grams == 69.0
    
    # Verify calorie calculation (protein: 4 cal/g, carbs: 4 cal/g, fats: 9 cal/g)
    calculated_calories = (
        float(meal_plan.protein_grams) * 4 +
        float(meal_plan.carbs_grams) * 4 +
        float(meal_plan.fats_grams) * 9
    )
    assert abs(calculated_calories - meal_plan.daily_calorie_target) < 100  # Within 100 cal tolerance
    
    # Verify we can query and retrieve the plan
    stmt = select(MealPlan).where(MealPlan.profile_id == profile.id)
    result = await db_session.execute(stmt)
    retrieved_plan = result.scalars().first()
    
    assert retrieved_plan is not None
    assert retrieved_plan.protein_grams == 188.0
    assert retrieved_plan.carbs_grams == 281.0
    assert retrieved_plan.fats_grams == 69.0


@pytest.mark.asyncio
async def test_agent_context_to_database_mapping(db_session: AsyncSession):
    """Test complete flow: agent context → database models."""
    # Create user and profile
    user = User(
        email="test_mapping@example.com",
        hashed_password="test_hash",
        full_name="Test Mapping User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    profile = UserProfile(
        user_id=user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Simulate agent_context from onboarding
    agent_context = {
        "workout_planning": {
            "proposed_plan": {
                "frequency": 4,
                "location": "gym",
                "duration_minutes": 75,
                "equipment": ["barbell", "dumbbells"],
                "training_split": "push_pull_legs",
                "exercises": [
                    {"day": 1, "name": "Bench Press", "sets": 4, "reps": "8-10"},
                    {"day": 2, "name": "Deadlift", "sets": 3, "reps": "5-8"}
                ]
            },
            "user_approved": True
        },
        "diet_planning": {
            "proposed_plan": {
                "daily_calories": 2800,
                "protein_g": 210,
                "carbs_g": 350,
                "fats_g": 75,
                "meal_frequency": 4,
                "sample_meals": [
                    {"name": "Breakfast", "calories": 700},
                    {"name": "Lunch", "calories": 800}
                ]
            },
            "user_approved": True
        }
    }
    
    # Map workout plan (1:1 mapping - no parsing needed)
    workout_plan = WorkoutPlan(
        user_id=user.id,
        plan_name="Push/Pull/Legs Split",
        duration_weeks=12,
        days_per_week=agent_context["workout_planning"]["proposed_plan"]["frequency"],
        plan_data=agent_context["workout_planning"]["proposed_plan"]  # Direct JSONB storage
    )
    db_session.add(workout_plan)
    
    # Map meal plan (1:1 mapping - no conversion needed)
    meal_plan_data = agent_context["diet_planning"]["proposed_plan"]
    meal_plan = MealPlan(
        profile_id=profile.id,
        daily_calorie_target=meal_plan_data["daily_calories"],
        protein_grams=meal_plan_data["protein_g"],  # Direct mapping
        carbs_grams=meal_plan_data["carbs_g"],      # Direct mapping
        fats_grams=meal_plan_data["fats_g"]         # Direct mapping
    )
    db_session.add(meal_plan)
    
    await db_session.commit()
    await db_session.refresh(workout_plan)
    await db_session.refresh(meal_plan)
    
    # Verify workout plan mapping
    assert workout_plan.plan_data["frequency"] == 4
    assert workout_plan.plan_data["training_split"] == "push_pull_legs"
    assert len(workout_plan.plan_data["exercises"]) == 2
    
    # Verify meal plan mapping
    assert meal_plan.daily_calorie_target == 2800
    assert meal_plan.protein_grams == 210
    assert meal_plan.carbs_grams == 350
    assert meal_plan.fats_grams == 75
    
    print("✅ Agent context → Database mapping successful!")
    print(f"   Workout plan stored with {len(workout_plan.plan_data['exercises'])} exercises")
    print(f"   Meal plan: {meal_plan.daily_calorie_target} cal, {meal_plan.protein_grams}g protein")


@pytest.mark.asyncio
async def test_plan_data_nullable(db_session: AsyncSession):
    """Test that plan_data can be null (for backward compatibility)."""
    user = User(
        email="test_nullable@example.com",
        hashed_password="test_hash",
        full_name="Test Nullable User",
        is_active=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    
    # Create WorkoutPlan without plan_data (should work for backward compatibility)
    workout_plan = WorkoutPlan(
        user_id=user.id,
        plan_name="Legacy Plan",
        duration_weeks=8,
        days_per_week=3,
        plan_data=None  # Nullable
    )
    
    db_session.add(workout_plan)
    await db_session.commit()
    await db_session.refresh(workout_plan)
    
    assert workout_plan.plan_data is None
    assert workout_plan.plan_name == "Legacy Plan"
