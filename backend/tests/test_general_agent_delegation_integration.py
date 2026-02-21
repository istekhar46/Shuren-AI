"""
Integration tests for General Assistant Agent delegation tools.

This module tests end-to-end functionality of the delegation tools added to
the General Assistant Agent, verifying that tools correctly query the database
and return properly formatted responses.

Test Categories:
- @pytest.mark.integration - Integration tests requiring database
- @pytest.mark.asyncio - Async test execution
"""

import pytest
import json
from datetime import datetime, time, timezone
from uuid import uuid4
from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.general_assistant import GeneralAssistantAgent
from app.agents.context import AgentContext
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    WorkoutSchedule,
    MealSchedule,
    MealPlan,
    DietaryPreference
)
from app.models.workout import (
    WorkoutPlan,
    WorkoutDay,
    WorkoutExercise,
    ExerciseLibrary
)
from app.models.meal_template import MealTemplate, TemplateMeal
from app.models.dish import Dish, DishIngredient, Ingredient


# ============================================================================
# Test Markers
# ============================================================================

pytestmark = [
    pytest.mark.asyncio,
    pytest.mark.integration,
]



# ============================================================================
# Integration Tests - get_workout_info Tool
# ============================================================================

async def test_get_workout_info_with_valid_workout(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_workout_info tool retrieves today's workout end-to-end.
    
    Validates: FR-1, US-1.1, US-1.2, US-1.3
    """
    # Create UserProfile
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create WorkoutSchedule for today
    current_day = datetime.now().weekday()
    workout_schedule = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile.id,
        day_of_week=current_day,
        scheduled_time=time(18, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_schedule)
    
    # Create WorkoutPlan
    workout_plan = WorkoutPlan(
        id=uuid4(),
        user_id=test_user.id,
        plan_name="Test Workout Plan",
        days_per_week=4,
        duration_weeks=12,
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_plan)
    
    # Create ExerciseLibrary entries
    exercise1 = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Bench Press",
        exercise_slug="bench-press",
        exercise_type="strength",
        primary_muscle_group="chest",
        difficulty_level="intermediate",
        description="Chest exercise",
        instructions="Lie on bench and press",
        created_at=datetime.now(timezone.utc)
    )
    exercise2 = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Squats",
        exercise_slug="squats",
        exercise_type="strength",
        primary_muscle_group="legs",
        difficulty_level="intermediate",
        description="Leg exercise",
        instructions="Squat down and up",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(exercise1)
    db_session.add(exercise2)
    await db_session.flush()
    
    # Create WorkoutDay for today
    day_number = current_day + 1
    workout_day = WorkoutDay(
        id=uuid4(),
        workout_plan_id=workout_plan.id,
        day_number=day_number,
        day_name="Push Day",
        muscle_groups=["chest", "shoulders", "triceps"],
        workout_type="strength",
        estimated_duration_minutes=60,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_day)
    await db_session.flush()
    
    # Create WorkoutExercises
    workout_exercise1 = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day.id,
        exercise_library_id=exercise1.id,
        exercise_order=1,
        sets=4,
        reps_min=8,
        reps_max=12,
        rest_seconds=90,
        created_at=datetime.now(timezone.utc)
    )
    workout_exercise2 = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day.id,
        exercise_library_id=exercise2.id,
        exercise_order=2,
        sets=3,
        reps_target=10,
        weight_kg=Decimal("80.0"),
        rest_seconds=120,
        notes="Focus on form",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_exercise1)
    db_session.add(workout_exercise2)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_workout_info
    tools = agent.get_tools()
    workout_tool = next(t for t in tools if t.name == "get_workout_info")
    
    # Call tool
    result = await workout_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify workout details
    workout_data = data["data"]
    assert workout_data["day_name"] == "Push Day"
    assert workout_data["workout_type"] == "strength"
    assert "chest" in workout_data["muscle_groups"]
    assert workout_data["estimated_duration_minutes"] == 60
    
    # Verify exercises
    assert len(workout_data["exercises"]) == 2
    
    exercise1_data = workout_data["exercises"][0]
    assert exercise1_data["name"] == "Bench Press"
    assert exercise1_data["sets"] == 4
    assert exercise1_data["reps"] == "8-12"
    assert exercise1_data["rest_seconds"] == 90
    
    exercise2_data = workout_data["exercises"][1]
    assert exercise2_data["name"] == "Squats"
    assert exercise2_data["sets"] == 3
    assert exercise2_data["reps"] == "10"
    assert exercise2_data["weight_kg"] == 80.0
    assert exercise2_data["rest_seconds"] == 120
    assert exercise2_data["notes"] == "Focus on form"
    
    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "general_assistant_agent"


async def test_get_workout_info_rest_day(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_workout_info when no workout scheduled (rest day).
    
    Validates: FR-1, US-1.4
    """
    # Create UserProfile without workout schedule for today
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_workout_info
    tools = agent.get_tools()
    workout_tool = next(t for t in tools if t.name == "get_workout_info")
    
    # Call tool
    result = await workout_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with rest day message
    assert data["success"] is True
    assert "data" in data
    assert "message" in data["data"]
    assert "rest day" in data["data"]["message"].lower()


async def test_get_workout_info_user_not_found(
    db_session: AsyncSession
):
    """Test get_workout_info handles missing user profile gracefully.
    
    Validates: NFR-3 (Error Handling)
    """
    # Create AgentContext with non-existent user
    fake_user_id = str(uuid4())
    context = AgentContext(
        user_id=fake_user_id,
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_workout_info
    tools = agent.get_tools()
    workout_tool = next(t for t in tools if t.name == "get_workout_info")
    
    # Call tool
    result = await workout_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "profile not found" in data["error"].lower()



# ============================================================================
# Integration Tests - get_meal_info Tool
# ============================================================================

async def test_get_meal_info_with_valid_meal_plan(
    db_session: AsyncSession,
    test_user: User,
    sample_ingredients: list
):
    """Test get_meal_info tool retrieves today's meal plan end-to-end.
    
    Validates: FR-2, US-2.1, US-2.2, US-2.3
    """
    # Create UserProfile
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create MealPlan
    meal_plan = MealPlan(
        id=uuid4(),
        profile_id=profile.id,
        daily_calorie_target=2500,
        protein_percentage=Decimal("30.0"),
        carbs_percentage=Decimal("45.0"),
        fats_percentage=Decimal("25.0"),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_plan)
    
    # Create MealSchedules
    breakfast_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    lunch_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(breakfast_schedule)
    db_session.add(lunch_schedule)
    
    # Create Dishes
    breakfast_dish = Dish(
        id=uuid4(),
        name="Oatmeal with Banana",
        name_hindi="ओट्स और केला",
        cuisine_type="continental",
        meal_type="breakfast",
        serving_size_g=Decimal("250"),
        calories=Decimal("350"),
        protein_g=Decimal("12"),
        carbs_g=Decimal("60"),
        fats_g=Decimal("8"),
        prep_time_minutes=5,
        cook_time_minutes=5,
        difficulty_level="easy",
        is_vegetarian=True,
        is_vegan=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    lunch_dish = Dish(
        id=uuid4(),
        name="Grilled Chicken with Rice",
        name_hindi="ग्रिल्ड चिकन और चावल",
        cuisine_type="continental",
        meal_type="lunch",
        serving_size_g=Decimal("400"),
        calories=Decimal("550"),
        protein_g=Decimal("45"),
        carbs_g=Decimal("55"),
        fats_g=Decimal("12"),
        prep_time_minutes=10,
        cook_time_minutes=25,
        difficulty_level="medium",
        is_vegetarian=False,
        is_vegan=False,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(breakfast_dish)
    db_session.add(lunch_dish)
    await db_session.flush()
    
    # Create MealTemplate
    meal_template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_template)
    await db_session.flush()
    
    # Create TemplateMeals for today
    current_day = datetime.now().weekday()
    
    template_meal1 = TemplateMeal(
        id=uuid4(),
        template_id=meal_template.id,
        meal_schedule_id=breakfast_schedule.id,
        dish_id=breakfast_dish.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    template_meal2 = TemplateMeal(
        id=uuid4(),
        template_id=meal_template.id,
        meal_schedule_id=lunch_schedule.id,
        dish_id=lunch_dish.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(template_meal1)
    db_session.add(template_meal2)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_meal_info
    tools = agent.get_tools()
    meal_tool = next(t for t in tools if t.name == "get_meal_info")
    
    # Call tool
    result = await meal_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify meal plan details
    meal_data = data["data"]
    assert meal_data["day_of_week"] == current_day
    
    # Verify meals
    assert len(meal_data["meals"]) == 2
    
    breakfast_data = meal_data["meals"][0]
    assert breakfast_data["meal_name"] == "breakfast"
    assert breakfast_data["dish_name"] == "Oatmeal with Banana"
    assert breakfast_data["calories"] == 350.0
    assert breakfast_data["protein_g"] == 12.0
    assert breakfast_data["is_vegetarian"] is True
    assert breakfast_data["is_vegan"] is True
    
    lunch_data = meal_data["meals"][1]
    assert lunch_data["meal_name"] == "lunch"
    assert lunch_data["dish_name"] == "Grilled Chicken with Rice"
    assert lunch_data["calories"] == 550.0
    assert lunch_data["protein_g"] == 45.0
    
    # Verify daily totals
    assert "daily_totals" in meal_data
    assert meal_data["daily_totals"]["calories"] == 900.0
    assert meal_data["daily_totals"]["protein_g"] == 57.0
    
    # Verify targets
    assert "targets" in meal_data
    assert meal_data["targets"]["daily_calorie_target"] == 2500
    assert meal_data["targets"]["protein_percentage"] == 30.0
    
    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "general_assistant_agent"


async def test_get_meal_info_no_meal_plan(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_meal_info when no meal plan configured.
    
    Validates: FR-2, US-2.4
    """
    # Create UserProfile without meal plan
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_meal_info
    tools = agent.get_tools()
    meal_tool = next(t for t in tools if t.name == "get_meal_info")
    
    # Call tool
    result = await meal_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with helpful message
    assert data["success"] is True
    assert "data" in data
    assert "message" in data["data"]
    assert "meal plan" in data["data"]["message"].lower()


async def test_get_meal_info_user_not_found(
    db_session: AsyncSession
):
    """Test get_meal_info handles missing user profile gracefully.
    
    Validates: NFR-3 (Error Handling)
    """
    # Create AgentContext with non-existent user
    fake_user_id = str(uuid4())
    context = AgentContext(
        user_id=fake_user_id,
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_meal_info
    tools = agent.get_tools()
    meal_tool = next(t for t in tools if t.name == "get_meal_info")
    
    # Call tool
    result = await meal_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "profile not found" in data["error"].lower()



# ============================================================================
# Integration Tests - get_schedule_info Tool
# ============================================================================

async def test_get_schedule_info_with_valid_schedules(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_schedule_info tool retrieves schedules end-to-end.
    
    Validates: FR-3, US-3.1, US-3.2, US-3.3
    """
    # Create UserProfile
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    await db_session.flush()
    
    # Create WorkoutSchedules
    workout_schedule1 = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile.id,
        day_of_week=1,  # Tuesday
        scheduled_time=time(18, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    workout_schedule2 = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile.id,
        day_of_week=3,  # Thursday
        scheduled_time=time(18, 30),
        enable_notifications=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_schedule1)
    db_session.add(workout_schedule2)
    
    # Create MealSchedules
    meal_schedule1 = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    meal_schedule2 = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    meal_schedule3 = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="dinner",
        scheduled_time=time(19, 30),
        enable_notifications=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_schedule1)
    db_session.add(meal_schedule2)
    db_session.add(meal_schedule3)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_schedule_info
    tools = agent.get_tools()
    schedule_tool = next(t for t in tools if t.name == "get_schedule_info")
    
    # Call tool
    result = await schedule_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify schedule details
    schedule_data = data["data"]
    
    # Verify workout schedules
    assert "workouts" in schedule_data
    assert len(schedule_data["workouts"]) == 2
    
    workout1 = schedule_data["workouts"][0]
    assert workout1["day"] == "Tuesday"
    assert workout1["day_of_week"] == 1
    assert workout1["time"] == "18:00:00"
    assert workout1["notifications_enabled"] is True
    
    workout2 = schedule_data["workouts"][1]
    assert workout2["day"] == "Thursday"
    assert workout2["day_of_week"] == 3
    assert workout2["time"] == "18:30:00"
    assert workout2["notifications_enabled"] is False
    
    # Verify meal schedules
    assert "meals" in schedule_data
    assert len(schedule_data["meals"]) == 3
    
    meal1 = schedule_data["meals"][0]
    assert meal1["meal_name"] == "breakfast"
    assert meal1["time"] == "08:00:00"
    assert meal1["notifications_enabled"] is True
    
    meal2 = schedule_data["meals"][1]
    assert meal2["meal_name"] == "lunch"
    assert meal2["time"] == "13:00:00"
    
    meal3 = schedule_data["meals"][2]
    assert meal3["meal_name"] == "dinner"
    assert meal3["time"] == "19:30:00"
    assert meal3["notifications_enabled"] is False
    
    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "general_assistant_agent"


async def test_get_schedule_info_no_schedules(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_schedule_info when no schedules configured.
    
    Validates: FR-3
    """
    # Create UserProfile without schedules
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="general_fitness"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_schedule_info
    tools = agent.get_tools()
    schedule_tool = next(t for t in tools if t.name == "get_schedule_info")
    
    # Call tool
    result = await schedule_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with empty schedules
    assert data["success"] is True
    assert "data" in data
    assert data["data"]["workouts"] == []
    assert data["data"]["meals"] == []


async def test_get_schedule_info_user_not_found(
    db_session: AsyncSession
):
    """Test get_schedule_info handles missing user profile gracefully.
    
    Validates: NFR-3 (Error Handling)
    """
    # Create AgentContext with non-existent user
    fake_user_id = str(uuid4())
    context = AgentContext(
        user_id=fake_user_id,
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_schedule_info
    tools = agent.get_tools()
    schedule_tool = next(t for t in tools if t.name == "get_schedule_info")
    
    # Call tool
    result = await schedule_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "profile not found" in data["error"].lower()



# ============================================================================
# Integration Tests - get_exercise_demo Tool
# ============================================================================

async def test_get_exercise_demo_with_valid_exercise(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_exercise_demo tool retrieves exercise details end-to-end.
    
    Validates: FR-4, US-4.1, US-4.2, US-4.3
    """
    # Create ExerciseLibrary entries
    exercise1 = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Bench Press",
        exercise_slug="bench-press",
        exercise_type="strength",
        primary_muscle_group="chest",
        secondary_muscle_groups=["shoulders", "triceps"],
        difficulty_level="intermediate",
        description="Classic chest exercise performed on a bench",
        instructions="Lie on bench, lower bar to chest, press up",
        gif_url="https://example.com/bench-press.gif",
        video_url="https://example.com/bench-press.mp4",
        created_at=datetime.now(timezone.utc)
    )
    exercise2 = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Squats",
        exercise_slug="squats",
        exercise_type="strength",
        primary_muscle_group="legs",
        secondary_muscle_groups=["glutes", "core"],
        difficulty_level="beginner",
        description="Fundamental leg exercise",
        instructions="Stand with feet shoulder-width, squat down, stand up",
        gif_url="https://example.com/squats.gif",
        video_url="https://example.com/squats.mp4",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(exercise1)
    db_session.add(exercise2)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_exercise_demo
    tools = agent.get_tools()
    exercise_tool = next(t for t in tools if t.name == "get_exercise_demo")
    
    # Call tool with exact match
    result = await exercise_tool.ainvoke({"exercise_name": "Bench Press"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify exercise details
    exercise_data = data["data"]
    assert exercise_data["exercise_name"] == "Bench Press"
    assert exercise_data["primary_muscle_group"] == "chest"
    assert exercise_data["difficulty_level"] == "intermediate"
    assert exercise_data["description"] == "Classic chest exercise performed on a bench"
    assert exercise_data["instructions"] == "Lie on bench, lower bar to chest, press up"
    assert exercise_data["gif_url"] == "https://example.com/bench-press.gif"
    assert exercise_data["video_url"] == "https://example.com/bench-press.mp4"
    
    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "general_assistant_agent"


async def test_get_exercise_demo_partial_match(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_exercise_demo with case-insensitive partial match.
    
    Validates: FR-4, US-4.1, US-4.2
    """
    # Create ExerciseLibrary entry
    exercise = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Dumbbell Shoulder Press",
        exercise_slug="dumbbell-shoulder-press",
        exercise_type="strength",
        primary_muscle_group="shoulders",
        difficulty_level="intermediate",
        description="Shoulder exercise with dumbbells",
        instructions="Press dumbbells overhead",
        gif_url="https://example.com/shoulder-press.gif",
        video_url="https://example.com/shoulder-press.mp4",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(exercise)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_exercise_demo
    tools = agent.get_tools()
    exercise_tool = next(t for t in tools if t.name == "get_exercise_demo")
    
    # Call tool with partial match (case-insensitive)
    result = await exercise_tool.ainvoke({"exercise_name": "shoulder press"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify exercise found
    exercise_data = data["data"]
    assert exercise_data["exercise_name"] == "Dumbbell Shoulder Press"
    assert exercise_data["primary_muscle_group"] == "shoulders"


async def test_get_exercise_demo_not_found(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_exercise_demo when exercise not found.
    
    Validates: FR-4, US-4.4
    """
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="general_fitness"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_exercise_demo
    tools = agent.get_tools()
    exercise_tool = next(t for t in tools if t.name == "get_exercise_demo")
    
    # Call tool with non-existent exercise
    result = await exercise_tool.ainvoke({"exercise_name": "Nonexistent Exercise"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with helpful message
    assert data["success"] is True
    assert "data" in data
    assert "message" in data["data"]
    assert "not found" in data["data"]["message"].lower()
    assert "Nonexistent Exercise" in data["data"]["message"]



# ============================================================================
# Integration Tests - get_recipe_details Tool
# ============================================================================

async def test_get_recipe_details_with_valid_dish(
    db_session: AsyncSession,
    test_user: User,
    sample_ingredients: list
):
    """Test get_recipe_details tool retrieves recipe details end-to-end.
    
    Validates: FR-5, US-5.1, US-5.2, US-5.3
    """
    # Get ingredients by name for easy reference
    ingredients_map = {ing.name: ing for ing in sample_ingredients}
    
    # Create Dish
    dish = Dish(
        id=uuid4(),
        name="Paneer Tikka Masala",
        name_hindi="पनीर टिक्का मसाला",
        description="Creamy Indian curry with paneer",
        cuisine_type="north_indian",
        meal_type="dinner",
        difficulty_level="medium",
        serving_size_g=Decimal("350"),
        calories=Decimal("480"),
        protein_g=Decimal("25"),
        carbs_g=Decimal("35"),
        fats_g=Decimal("22"),
        fiber_g=Decimal("6"),
        prep_time_minutes=20,
        cook_time_minutes=30,
        is_vegetarian=True,
        is_vegan=False,
        is_gluten_free=True,
        is_dairy_free=False,
        is_nut_free=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(dish)
    await db_session.flush()
    
    # Create DishIngredients
    paneer = ingredients_map.get("paneer")
    tomato = ingredients_map.get("tomato")
    turmeric = ingredients_map.get("turmeric")
    
    if paneer:
        dish_ingredient1 = DishIngredient(
            id=uuid4(),
            dish_id=dish.id,
            ingredient_id=paneer.id,
            quantity=Decimal("200"),
            unit="g",
            preparation_note="Cut into cubes",
            is_optional=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish_ingredient1)
    
    if tomato:
        dish_ingredient2 = DishIngredient(
            id=uuid4(),
            dish_id=dish.id,
            ingredient_id=tomato.id,
            quantity=Decimal("150"),
            unit="g",
            preparation_note="Pureed",
            is_optional=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish_ingredient2)
    
    if turmeric:
        dish_ingredient3 = DishIngredient(
            id=uuid4(),
            dish_id=dish.id,
            ingredient_id=turmeric.id,
            quantity=Decimal("1"),
            unit="tsp",
            preparation_note=None,
            is_optional=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish_ingredient3)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with exact match
    result = await recipe_tool.ainvoke({"dish_name": "Paneer Tikka Masala"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify recipe details
    recipe_data = data["data"]
    assert recipe_data["dish_name"] == "Paneer Tikka Masala"
    assert recipe_data["dish_name_hindi"] == "पनीर टिक्का मसाला"
    assert recipe_data["description"] == "Creamy Indian curry with paneer"
    assert recipe_data["cuisine_type"] == "north_indian"
    assert recipe_data["meal_type"] == "dinner"
    assert recipe_data["difficulty_level"] == "medium"
    assert recipe_data["prep_time_minutes"] == 20
    assert recipe_data["cook_time_minutes"] == 30
    assert recipe_data["serving_size_g"] == 350.0
    
    # Verify nutrition
    assert "nutrition" in recipe_data
    nutrition = recipe_data["nutrition"]
    assert nutrition["calories"] == 480.0
    assert nutrition["protein_g"] == 25.0
    assert nutrition["carbs_g"] == 35.0
    assert nutrition["fats_g"] == 22.0
    assert nutrition["fiber_g"] == 6.0
    
    # Verify dietary tags
    assert "dietary_tags" in recipe_data
    tags = recipe_data["dietary_tags"]
    assert tags["is_vegetarian"] is True
    assert tags["is_vegan"] is False
    assert tags["is_gluten_free"] is True
    assert tags["is_dairy_free"] is False
    assert tags["is_nut_free"] is True
    
    # Verify ingredients
    assert "ingredients" in recipe_data
    ingredients = recipe_data["ingredients"]
    assert len(ingredients) == 3
    
    # Check paneer ingredient
    paneer_ing = next((i for i in ingredients if i["name"] == "paneer"), None)
    assert paneer_ing is not None
    assert paneer_ing["quantity"] == 200.0
    assert paneer_ing["unit"] == "g"
    assert paneer_ing["preparation_note"] == "Cut into cubes"
    assert paneer_ing["is_optional"] is False
    
    # Check tomato ingredient
    tomato_ing = next((i for i in ingredients if i["name"] == "tomato"), None)
    assert tomato_ing is not None
    assert tomato_ing["quantity"] == 150.0
    assert tomato_ing["unit"] == "g"
    assert tomato_ing["preparation_note"] == "Pureed"
    
    # Check turmeric ingredient (optional)
    turmeric_ing = next((i for i in ingredients if i["name"] == "turmeric"), None)
    assert turmeric_ing is not None
    assert turmeric_ing["is_optional"] is True
    
    # Verify metadata
    assert "metadata" in data
    assert data["metadata"]["source"] == "general_assistant_agent"


async def test_get_recipe_details_partial_match(
    db_session: AsyncSession,
    test_user: User,
    sample_ingredients: list
):
    """Test get_recipe_details with case-insensitive partial match.
    
    Validates: FR-5, US-5.1, US-5.2
    """
    # Create Dish
    dish = Dish(
        id=uuid4(),
        name="Dal Tadka",
        name_hindi="दाल तड़का",
        description="Tempered lentil curry",
        cuisine_type="north_indian",
        meal_type="lunch",
        difficulty_level="easy",
        serving_size_g=Decimal("300"),
        calories=Decimal("250"),
        protein_g=Decimal("15"),
        carbs_g=Decimal("40"),
        fats_g=Decimal("5"),
        prep_time_minutes=10,
        cook_time_minutes=25,
        is_vegetarian=True,
        is_vegan=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(dish)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with partial match (case-insensitive)
    result = await recipe_tool.ainvoke({"dish_name": "dal"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Verify recipe found
    recipe_data = data["data"]
    assert recipe_data["dish_name"] == "Dal Tadka"
    assert recipe_data["cuisine_type"] == "north_indian"


async def test_get_recipe_details_not_found(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_recipe_details when recipe not found.
    
    Validates: FR-5, US-5.4
    """
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="general_fitness"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with non-existent recipe
    result = await recipe_tool.ainvoke({"dish_name": "Nonexistent Recipe"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with helpful message
    assert data["success"] is True
    assert "data" in data
    assert "message" in data["data"]
    assert "not found" in data["data"]["message"].lower()
    assert "Nonexistent Recipe" in data["data"]["message"]



# ============================================================================
# Property-Based Tests - User Data Isolation
# ============================================================================

async def test_property_user_data_isolation_workout(
    db_session: AsyncSession
):
    """Property test: get_workout_info only returns data for specified user.
    
    Feature: general-agent-delegation-tools, Property 7: User Data Isolation
    Validates: Requirements TC-2
    """
    # Create two users with different workout plans
    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        hashed_password="hash1",
        full_name="User One",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        hashed_password="hash2",
        full_name="User Two",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user1)
    db_session.add(user2)
    
    # Create profiles
    profile1 = UserProfile(
        id=uuid4(),
        user_id=user1.id,
        fitness_level="beginner",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    profile2 = UserProfile(
        id=uuid4(),
        user_id=user2.id,
        fitness_level="advanced",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile1)
    db_session.add(profile2)
    
    # Create workout schedules for today
    current_day = datetime.now().weekday()
    
    schedule1 = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile1.id,
        day_of_week=current_day,
        scheduled_time=time(18, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    schedule2 = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile2.id,
        day_of_week=current_day,
        scheduled_time=time(19, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(schedule1)
    db_session.add(schedule2)
    
    # Create workout plans with different names
    workout_plan1 = WorkoutPlan(
        id=uuid4(),
        user_id=user1.id,
        plan_name="Beginner Plan",
        days_per_week=3,
        duration_weeks=8,
        created_at=datetime.now(timezone.utc)
    )
    workout_plan2 = WorkoutPlan(
        id=uuid4(),
        user_id=user2.id,
        plan_name="Advanced Plan",
        days_per_week=5,
        duration_weeks=12,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_plan1)
    db_session.add(workout_plan2)
    
    # Create exercise
    exercise = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Push-ups",
        exercise_slug="push-ups",
        exercise_type="strength",
        primary_muscle_group="chest",
        difficulty_level="beginner",
        description="Basic push-up",
        instructions="Lower and push up",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(exercise)
    await db_session.flush()
    
    # Create workout days with different names
    day_number = current_day + 1
    
    workout_day1 = WorkoutDay(
        id=uuid4(),
        workout_plan_id=workout_plan1.id,
        day_number=day_number,
        day_name="Beginner Day",
        muscle_groups=["chest"],
        workout_type="strength",
        created_at=datetime.now(timezone.utc)
    )
    workout_day2 = WorkoutDay(
        id=uuid4(),
        workout_plan_id=workout_plan2.id,
        day_number=day_number,
        day_name="Advanced Day",
        muscle_groups=["chest", "back"],
        workout_type="strength",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_day1)
    db_session.add(workout_day2)
    await db_session.flush()
    
    # Create workout exercises
    workout_exercise1 = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day1.id,
        exercise_library_id=exercise.id,
        exercise_order=1,
        sets=3,
        reps_target=10,
        created_at=datetime.now(timezone.utc)
    )
    workout_exercise2 = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day2.id,
        exercise_library_id=exercise.id,
        exercise_order=1,
        sets=5,
        reps_target=20,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_exercise1)
    db_session.add(workout_exercise2)
    
    await db_session.commit()
    
    # Test user1 can only see their own workout
    context1 = AgentContext(
        user_id=str(user1.id),
        fitness_level="beginner",
        primary_goal="general_fitness"
    )
    agent1 = GeneralAssistantAgent(context=context1, db_session=db_session)
    tools1 = agent1.get_tools()
    workout_tool1 = next(t for t in tools1 if t.name == "get_workout_info")
    
    result1 = await workout_tool1.ainvoke({})
    data1 = json.loads(result1)
    
    assert data1["success"] is True
    assert data1["data"]["day_name"] == "Beginner Day"
    assert data1["data"]["exercises"][0]["sets"] == 3
    assert data1["data"]["exercises"][0]["reps"] == "10"
    
    # Test user2 can only see their own workout
    context2 = AgentContext(
        user_id=str(user2.id),
        fitness_level="advanced",
        primary_goal="muscle_gain"
    )
    agent2 = GeneralAssistantAgent(context=context2, db_session=db_session)
    tools2 = agent2.get_tools()
    workout_tool2 = next(t for t in tools2 if t.name == "get_workout_info")
    
    result2 = await workout_tool2.ainvoke({})
    data2 = json.loads(result2)
    
    assert data2["success"] is True
    assert data2["data"]["day_name"] == "Advanced Day"
    assert data2["data"]["exercises"][0]["sets"] == 5
    assert data2["data"]["exercises"][0]["reps"] == "20"
    
    # Property: Users never see each other's data
    assert data1["data"]["day_name"] != data2["data"]["day_name"]
    assert data1["data"]["exercises"][0]["sets"] != data2["data"]["exercises"][0]["sets"]


async def test_property_user_data_isolation_meal(
    db_session: AsyncSession,
    sample_ingredients: list
):
    """Property test: get_meal_info only returns data for specified user.
    
    Feature: general-agent-delegation-tools, Property 7: User Data Isolation
    Validates: Requirements TC-2
    """
    # Create two users with different meal plans
    user1 = User(
        id=uuid4(),
        email="user1@example.com",
        hashed_password="hash1",
        full_name="User One",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    user2 = User(
        id=uuid4(),
        email="user2@example.com",
        hashed_password="hash2",
        full_name="User Two",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user1)
    db_session.add(user2)
    
    # Create profiles
    profile1 = UserProfile(
        id=uuid4(),
        user_id=user1.id,
        fitness_level="beginner",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    profile2 = UserProfile(
        id=uuid4(),
        user_id=user2.id,
        fitness_level="advanced",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile1)
    db_session.add(profile2)
    
    # Create meal plans with different targets
    meal_plan1 = MealPlan(
        id=uuid4(),
        profile_id=profile1.id,
        daily_calorie_target=2000,
        protein_percentage=Decimal("25.0"),
        carbs_percentage=Decimal("50.0"),
        fats_percentage=Decimal("25.0"),
        created_at=datetime.now(timezone.utc)
    )
    meal_plan2 = MealPlan(
        id=uuid4(),
        profile_id=profile2.id,
        daily_calorie_target=3000,
        protein_percentage=Decimal("35.0"),
        carbs_percentage=Decimal("40.0"),
        fats_percentage=Decimal("25.0"),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_plan1)
    db_session.add(meal_plan2)
    
    # Create meal schedules
    schedule1 = MealSchedule(
        id=uuid4(),
        profile_id=profile1.id,
        meal_name="breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    schedule2 = MealSchedule(
        id=uuid4(),
        profile_id=profile2.id,
        meal_name="breakfast",
        scheduled_time=time(7, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(schedule1)
    db_session.add(schedule2)
    
    # Create different dishes
    dish1 = Dish(
        id=uuid4(),
        name="User1 Breakfast",
        cuisine_type="continental",
        meal_type="breakfast",
        serving_size_g=Decimal("200"),
        calories=Decimal("300"),
        protein_g=Decimal("15"),
        carbs_g=Decimal("40"),
        fats_g=Decimal("8"),
        prep_time_minutes=5,
        cook_time_minutes=5,
        difficulty_level="easy",
        is_vegetarian=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    dish2 = Dish(
        id=uuid4(),
        name="User2 Breakfast",
        cuisine_type="continental",
        meal_type="breakfast",
        serving_size_g=Decimal("300"),
        calories=Decimal("500"),
        protein_g=Decimal("30"),
        carbs_g=Decimal("50"),
        fats_g=Decimal("15"),
        prep_time_minutes=10,
        cook_time_minutes=10,
        difficulty_level="medium",
        is_vegetarian=False,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(dish1)
    db_session.add(dish2)
    await db_session.flush()
    
    # Create meal templates
    template1 = MealTemplate(
        id=uuid4(),
        profile_id=profile1.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        created_at=datetime.now(timezone.utc)
    )
    template2 = MealTemplate(
        id=uuid4(),
        profile_id=profile2.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(template1)
    db_session.add(template2)
    await db_session.flush()
    
    # Create template meals for today
    current_day = datetime.now().weekday()
    
    template_meal1 = TemplateMeal(
        id=uuid4(),
        template_id=template1.id,
        meal_schedule_id=schedule1.id,
        dish_id=dish1.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    template_meal2 = TemplateMeal(
        id=uuid4(),
        template_id=template2.id,
        meal_schedule_id=schedule2.id,
        dish_id=dish2.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(template_meal1)
    db_session.add(template_meal2)
    
    await db_session.commit()
    
    # Test user1 can only see their own meal plan
    context1 = AgentContext(
        user_id=str(user1.id),
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    agent1 = GeneralAssistantAgent(context=context1, db_session=db_session)
    tools1 = agent1.get_tools()
    meal_tool1 = next(t for t in tools1 if t.name == "get_meal_info")
    
    result1 = await meal_tool1.ainvoke({})
    data1 = json.loads(result1)
    
    assert data1["success"] is True
    assert data1["data"]["meals"][0]["dish_name"] == "User1 Breakfast"
    assert data1["data"]["targets"]["daily_calorie_target"] == 2000
    
    # Test user2 can only see their own meal plan
    context2 = AgentContext(
        user_id=str(user2.id),
        fitness_level="advanced",
        primary_goal="muscle_gain"
    )
    agent2 = GeneralAssistantAgent(context=context2, db_session=db_session)
    tools2 = agent2.get_tools()
    meal_tool2 = next(t for t in tools2 if t.name == "get_meal_info")
    
    result2 = await meal_tool2.ainvoke({})
    data2 = json.loads(result2)
    
    assert data2["success"] is True
    assert data2["data"]["meals"][0]["dish_name"] == "User2 Breakfast"
    assert data2["data"]["targets"]["daily_calorie_target"] == 3000
    
    # Property: Users never see each other's data
    assert data1["data"]["meals"][0]["dish_name"] != data2["data"]["meals"][0]["dish_name"]
    assert data1["data"]["targets"]["daily_calorie_target"] != data2["data"]["targets"]["daily_calorie_target"]



# ============================================================================
# Property-Based Tests - Soft Delete Filtering
# ============================================================================

async def test_property_soft_delete_filtering_workout(
    db_session: AsyncSession,
    test_user: User
):
    """Property test: Soft deleted workout data is excluded from results.
    
    Feature: general-agent-delegation-tools, Property 8: Soft Delete Filtering
    Validates: Requirements TC-1
    """
    # Create UserProfile
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create WorkoutSchedule for today
    current_day = datetime.now().weekday()
    workout_schedule = WorkoutSchedule(
        id=uuid4(),
        profile_id=profile.id,
        day_of_week=current_day,
        scheduled_time=time(18, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_schedule)
    
    # Create WorkoutPlan
    workout_plan = WorkoutPlan(
        id=uuid4(),
        user_id=test_user.id,
        plan_name="Active Plan",
        days_per_week=4,
        duration_weeks=12,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_plan)
    
    # Create ExerciseLibrary entries (one active, one soft deleted)
    exercise_active = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Active Exercise",
        exercise_slug="active-exercise",
        exercise_type="strength",
        primary_muscle_group="chest",
        difficulty_level="intermediate",
        description="Active exercise",
        instructions="Do this exercise",
        created_at=datetime.now(timezone.utc),
        deleted_at=None  # Active
    )
    exercise_deleted = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Deleted Exercise",
        exercise_slug="deleted-exercise",
        exercise_type="strength",
        primary_muscle_group="back",
        difficulty_level="intermediate",
        description="Deleted exercise",
        instructions="Don't do this",
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add(exercise_active)
    db_session.add(exercise_deleted)
    await db_session.flush()
    
    # Create WorkoutDay
    day_number = current_day + 1
    workout_day = WorkoutDay(
        id=uuid4(),
        workout_plan_id=workout_plan.id,
        day_number=day_number,
        day_name="Test Day",
        muscle_groups=["chest", "back"],
        workout_type="strength",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(workout_day)
    await db_session.flush()
    
    # Create WorkoutExercises (one with active exercise, one with deleted exercise)
    workout_exercise_active = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day.id,
        exercise_library_id=exercise_active.id,
        exercise_order=1,
        sets=4,
        reps_target=10,
        created_at=datetime.now(timezone.utc)
    )
    workout_exercise_deleted = WorkoutExercise(
        id=uuid4(),
        workout_day_id=workout_day.id,
        exercise_library_id=exercise_deleted.id,
        exercise_order=2,
        sets=3,
        reps_target=12,
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add(workout_exercise_active)
    db_session.add(workout_exercise_deleted)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_workout_info
    tools = agent.get_tools()
    workout_tool = next(t for t in tools if t.name == "get_workout_info")
    
    # Call tool
    result = await workout_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # Property: Only active exercises are returned (soft deleted excluded)
    exercises = data["data"]["exercises"]
    assert len(exercises) == 1
    assert exercises[0]["name"] == "Active Exercise"
    
    # Property: Soft deleted exercise is NOT in results
    exercise_names = [e["name"] for e in exercises]
    assert "Deleted Exercise" not in exercise_names


async def test_property_soft_delete_filtering_exercise_demo(
    db_session: AsyncSession,
    test_user: User
):
    """Property test: Soft deleted exercises excluded from exercise demo search.
    
    Feature: general-agent-delegation-tools, Property 8: Soft Delete Filtering
    Validates: Requirements TC-1
    """
    # Create ExerciseLibrary entries (one active, one soft deleted with similar name)
    exercise_active = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Bench Press",
        exercise_slug="bench-press-active",
        exercise_type="strength",
        primary_muscle_group="chest",
        difficulty_level="intermediate",
        description="Active bench press",
        instructions="Press the bar",
        gif_url="https://example.com/bench-press.gif",
        created_at=datetime.now(timezone.utc),
        deleted_at=None  # Active
    )
    exercise_deleted = ExerciseLibrary(
        id=uuid4(),
        exercise_name="Bench Press Old Version",
        exercise_slug="bench-press-old",
        exercise_type="strength",
        primary_muscle_group="chest",
        difficulty_level="intermediate",
        description="Deleted bench press",
        instructions="Old instructions",
        gif_url="https://example.com/bench-press-old.gif",
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add(exercise_active)
    db_session.add(exercise_deleted)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_exercise_demo
    tools = agent.get_tools()
    exercise_tool = next(t for t in tools if t.name == "get_exercise_demo")
    
    # Call tool with partial match that could match both
    result = await exercise_tool.ainvoke({"exercise_name": "bench"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # Property: Only active exercise is returned (soft deleted excluded)
    assert data["data"]["exercise_name"] == "Bench Press"
    assert data["data"]["description"] == "Active bench press"
    assert "Old Version" not in data["data"]["exercise_name"]


async def test_property_soft_delete_filtering_recipe(
    db_session: AsyncSession,
    test_user: User,
    sample_ingredients: list
):
    """Property test: Soft deleted dishes and ingredients excluded from recipe search.
    
    Feature: general-agent-delegation-tools, Property 8: Soft Delete Filtering
    Validates: Requirements TC-1
    """
    # Get ingredients
    ingredients_map = {ing.name: ing for ing in sample_ingredients}
    
    # Create Dishes (one active, one soft deleted)
    dish_active = Dish(
        id=uuid4(),
        name="Active Dal",
        cuisine_type="north_indian",
        meal_type="lunch",
        serving_size_g=Decimal("300"),
        calories=Decimal("250"),
        protein_g=Decimal("15"),
        carbs_g=Decimal("40"),
        fats_g=Decimal("5"),
        prep_time_minutes=10,
        cook_time_minutes=25,
        difficulty_level="easy",
        is_vegetarian=True,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        deleted_at=None  # Active
    )
    dish_deleted = Dish(
        id=uuid4(),
        name="Deleted Dal Recipe",
        cuisine_type="north_indian",
        meal_type="lunch",
        serving_size_g=Decimal("300"),
        calories=Decimal("250"),
        protein_g=Decimal("15"),
        carbs_g=Decimal("40"),
        fats_g=Decimal("5"),
        prep_time_minutes=10,
        cook_time_minutes=25,
        difficulty_level="easy",
        is_vegetarian=True,
        is_active=True,
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add(dish_active)
    db_session.add(dish_deleted)
    await db_session.flush()
    
    # Create DishIngredients for active dish
    turmeric = ingredients_map.get("turmeric")
    if turmeric:
        dish_ingredient = DishIngredient(
            id=uuid4(),
            dish_id=dish_active.id,
            ingredient_id=turmeric.id,
            quantity=Decimal("1"),
            unit="tsp",
            is_optional=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(dish_ingredient)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with partial match that could match both
    result = await recipe_tool.ainvoke({"dish_name": "dal"})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # Property: Only active dish is returned (soft deleted excluded)
    assert data["data"]["dish_name"] == "Active Dal"
    assert "Deleted" not in data["data"]["dish_name"]


async def test_property_soft_delete_filtering_meal_schedule(
    db_session: AsyncSession,
    test_user: User,
    sample_ingredients: list
):
    """Property test: Soft deleted meal schedules excluded from meal plan.
    
    Feature: general-agent-delegation-tools, Property 8: Soft Delete Filtering
    Validates: Requirements TC-1
    """
    # Create UserProfile
    profile = UserProfile(
        id=uuid4(),
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create MealPlan
    meal_plan = MealPlan(
        id=uuid4(),
        profile_id=profile.id,
        daily_calorie_target=2500,
        protein_percentage=Decimal("30.0"),
        carbs_percentage=Decimal("45.0"),
        fats_percentage=Decimal("25.0"),
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_plan)
    
    # Create MealSchedules (one active, one soft deleted)
    breakfast_schedule = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc),
        deleted_at=None  # Active
    )
    lunch_schedule_deleted = MealSchedule(
        id=uuid4(),
        profile_id=profile.id,
        meal_name="lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True,
        created_at=datetime.now(timezone.utc),
        deleted_at=datetime.now(timezone.utc)  # Soft deleted
    )
    db_session.add(breakfast_schedule)
    db_session.add(lunch_schedule_deleted)
    
    # Create Dishes
    breakfast_dish = Dish(
        id=uuid4(),
        name="Breakfast Dish",
        cuisine_type="continental",
        meal_type="breakfast",
        serving_size_g=Decimal("250"),
        calories=Decimal("350"),
        protein_g=Decimal("12"),
        carbs_g=Decimal("60"),
        fats_g=Decimal("8"),
        prep_time_minutes=5,
        cook_time_minutes=5,
        difficulty_level="easy",
        is_vegetarian=True,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    lunch_dish = Dish(
        id=uuid4(),
        name="Lunch Dish",
        cuisine_type="continental",
        meal_type="lunch",
        serving_size_g=Decimal("400"),
        calories=Decimal("550"),
        protein_g=Decimal("45"),
        carbs_g=Decimal("55"),
        fats_g=Decimal("12"),
        prep_time_minutes=10,
        cook_time_minutes=25,
        difficulty_level="medium",
        is_vegetarian=False,
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(breakfast_dish)
    db_session.add(lunch_dish)
    await db_session.flush()
    
    # Create MealTemplate
    meal_template = MealTemplate(
        id=uuid4(),
        profile_id=profile.id,
        week_number=1,
        is_active=True,
        generated_by="system",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(meal_template)
    await db_session.flush()
    
    # Create TemplateMeals for today
    current_day = datetime.now().weekday()
    
    template_meal_active = TemplateMeal(
        id=uuid4(),
        template_id=meal_template.id,
        meal_schedule_id=breakfast_schedule.id,
        dish_id=breakfast_dish.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    template_meal_deleted = TemplateMeal(
        id=uuid4(),
        template_id=meal_template.id,
        meal_schedule_id=lunch_schedule_deleted.id,
        dish_id=lunch_dish.id,
        day_of_week=current_day,
        is_primary=True,
        alternative_order=1,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(template_meal_active)
    db_session.add(template_meal_deleted)
    
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="muscle_gain"
    )
    
    # Create GeneralAssistantAgent
    agent = GeneralAssistantAgent(context=context, db_session=db_session)
    
    # Get tools and find get_meal_info
    tools = agent.get_tools()
    meal_tool = next(t for t in tools if t.name == "get_meal_info")
    
    # Call tool
    result = await meal_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # Property: Only meals with active schedules are returned (soft deleted excluded)
    meals = data["data"]["meals"]
    assert len(meals) == 1
    assert meals[0]["meal_name"] == "breakfast"
    assert meals[0]["dish_name"] == "Breakfast Dish"
    
    # Property: Soft deleted meal schedule is NOT in results
    meal_names = [m["meal_name"] for m in meals]
    assert "lunch" not in meal_names
