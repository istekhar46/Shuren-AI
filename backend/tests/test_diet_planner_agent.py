"""
Integration tests for Diet Planner Agent.

This module tests the DietPlannerAgent implementation including:
- Agent instantiation and configuration
- Tool execution with database operations
- Text and voice mode processing
- System prompt generation
- Error handling

Test Categories:
- @pytest.mark.unit - Unit tests for individual components
- @pytest.mark.integration - Integration tests requiring database
- @pytest.mark.asyncio - Async test execution
"""

import pytest
import json
from datetime import datetime, time

from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.diet_planner import DietPlannerAgent
from app.agents.context import AgentContext, AgentResponse
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    DietaryPreference,
    MealPlan,
    MealSchedule
)
from app.models.dish import Dish, Ingredient, DishIngredient
from app.models.meal_template import MealTemplate, TemplateMeal


# ============================================================================
# Test Markers
# ============================================================================

pytestmark = [
    pytest.mark.asyncio,  # All tests in this module are async
]


# ============================================================================
# Unit Tests - Agent Creation
# ============================================================================

@pytest.mark.unit
def test_diet_planner_agent_creation():
    """Test DietPlannerAgent can be instantiated with context."""
    # Create AgentContext
    context = AgentContext(
        user_id="test-user-123",
        fitness_level="intermediate",
        primary_goal="fat_loss",
        energy_level="medium"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context)
    
    # Assert agent is created
    assert agent is not None
    assert agent.context == context
    assert agent.context.user_id == "test-user-123"
    assert agent.context.fitness_level == "intermediate"
    assert agent.context.primary_goal == "fat_loss"


@pytest.mark.unit
def test_diet_planner_agent_tools():
    """Test DietPlannerAgent has all 4 required tools."""
    # Create AgentContext
    context = AgentContext(
        user_id="test-user-456",
        fitness_level="beginner",
        primary_goal="muscle_gain"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context)
    
    # Get tools
    tools = agent.get_tools()
    
    # Assert 4 tools are available
    assert len(tools) == 4
    
    # Assert tool names
    tool_names = [t.name for t in tools]
    assert "get_current_meal_plan" in tool_names
    assert "suggest_meal_substitution" in tool_names
    assert "get_recipe_details" in tool_names
    assert "calculate_nutrition" in tool_names


@pytest.mark.unit
def test_diet_planner_system_prompt_text_mode():
    """Test system prompt generation for text mode."""
    context = AgentContext(
        user_id="test-user-789",
        fitness_level="advanced",
        primary_goal="general_fitness"
    )
    
    agent = DietPlannerAgent(context=context)
    prompt = agent._system_prompt(voice_mode=False)
    
    # Assert prompt contains key elements
    assert "nutrition and meal planning assistant" in prompt.lower()
    assert "advanced" in prompt
    assert "general_fitness" in prompt
    assert "markdown" in prompt.lower()
    assert "detailed" in prompt.lower()


@pytest.mark.unit
def test_diet_planner_system_prompt_voice_mode():
    """Test system prompt generation for voice mode."""
    context = AgentContext(
        user_id="test-user-101",
        fitness_level="beginner",
        primary_goal="fat_loss"
    )
    
    agent = DietPlannerAgent(context=context)
    prompt = agent._system_prompt(voice_mode=True)
    
    # Assert prompt contains voice-specific guidance
    assert "concise" in prompt.lower()
    assert "75 words" in prompt.lower() or "30 seconds" in prompt.lower()


# ============================================================================
# Integration Tests - get_current_meal_plan Tool
# ============================================================================

@pytest.mark.integration
async def test_get_current_meal_plan_success(
    db_session: AsyncSession,
    test_user: User,
    sample_dishes: list
):
    """Test get_current_meal_plan tool retrieves today's meals."""
    # Create UserProfile
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create MealPlan
    meal_plan = MealPlan(
        profile_id=profile.id,
        daily_calorie_target=2000,
        protein_percentage=30.0,
        carbs_percentage=40.0,
        fats_percentage=30.0
    )
    db_session.add(meal_plan)
    
    # Create MealSchedules
    breakfast_schedule = MealSchedule(
        profile_id=profile.id,
        meal_name="breakfast",
        scheduled_time=time(8, 0),
        enable_notifications=True
    )
    lunch_schedule = MealSchedule(
        profile_id=profile.id,
        meal_name="lunch",
        scheduled_time=time(13, 0),
        enable_notifications=True
    )
    db_session.add(breakfast_schedule)
    db_session.add(lunch_schedule)
    await db_session.commit()
    await db_session.refresh(breakfast_schedule)
    await db_session.refresh(lunch_schedule)
    
    # Create MealTemplate
    meal_template = MealTemplate(
        profile_id=profile.id,
        week_number=1,
        is_active=True
    )
    db_session.add(meal_template)
    await db_session.commit()
    await db_session.refresh(meal_template)
    
    # Get today's day of week
    from datetime import date
    today = date.today().weekday()
    
    # Create TemplateMeals for today
    breakfast_dish = sample_dishes[0]  # First dish from fixtures
    lunch_dish = sample_dishes[1]  # Second dish from fixtures
    
    template_meal_breakfast = TemplateMeal(
        template_id=meal_template.id,
        meal_schedule_id=breakfast_schedule.id,
        dish_id=breakfast_dish.id,
        day_of_week=today,
        is_primary=True
    )
    template_meal_lunch = TemplateMeal(
        template_id=meal_template.id,
        meal_schedule_id=lunch_schedule.id,
        dish_id=lunch_dish.id,
        day_of_week=today,
        is_primary=True
    )
    db_session.add(template_meal_breakfast)
    db_session.add(template_meal_lunch)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find get_current_meal_plan
    tools = agent.get_tools()
    meal_plan_tool = next(t for t in tools if t.name == "get_current_meal_plan")
    
    # Call tool
    result = await meal_plan_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Assert meals are present
    assert "meals" in data["data"]
    assert len(data["data"]["meals"]) == 2
    
    # Assert daily totals are calculated
    assert "daily_totals" in data["data"]
    assert "calories" in data["data"]["daily_totals"]
    assert "protein_g" in data["data"]["daily_totals"]
    
    # Assert targets are included
    assert "targets" in data["data"]
    assert data["data"]["targets"]["daily_calorie_target"] == 2000


@pytest.mark.integration
async def test_get_current_meal_plan_no_template(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_current_meal_plan when no meal template exists."""
    # Create UserProfile without meal template
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="muscle_gain"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find get_current_meal_plan
    tools = agent.get_tools()
    meal_plan_tool = next(t for t in tools if t.name == "get_current_meal_plan")
    
    # Call tool
    result = await meal_plan_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success with message
    assert data["success"] is True
    assert "message" in data["data"]
    assert "meal plan" in data["data"]["message"].lower()
    assert "configured" in data["data"]["message"].lower()


# ============================================================================
# Integration Tests - suggest_meal_substitution Tool
# ============================================================================

@pytest.mark.integration
async def test_suggest_meal_substitution_vegetarian(
    db_session: AsyncSession,
    test_user: User,
    sample_dishes: list
):
    """Test suggest_meal_substitution respects vegetarian preference."""
    # Create UserProfile
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create DietaryPreference with vegetarian diet
    dietary_pref = DietaryPreference(
        profile_id=profile.id,
        diet_type="vegetarian",
        allergies=[],
        intolerances=[],
        dislikes=[]
    )
    db_session.add(dietary_pref)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find suggest_meal_substitution
    tools = agent.get_tools()
    substitution_tool = next(t for t in tools if t.name == "suggest_meal_substitution")
    
    # Call tool
    result = await substitution_tool.ainvoke({
        "meal_type": "breakfast",
        "reason": "want variety"
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # If suggestions exist, verify all are vegetarian
    if "suggestions" in data["data"] and len(data["data"]["suggestions"]) > 0:
        for suggestion in data["data"]["suggestions"]:
            assert suggestion["is_vegetarian"] is True
    
    # Assert dietary context is included
    assert "dietary_context" in data["data"]
    assert data["data"]["dietary_context"]["diet_type"] == "vegetarian"


@pytest.mark.integration
async def test_suggest_meal_substitution_with_allergies(
    db_session: AsyncSession,
    test_user: User,
    sample_dishes: list
):
    """Test suggest_meal_substitution excludes allergens."""
    # Create UserProfile
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    await db_session.refresh(profile)
    
    # Create DietaryPreference with allergies
    dietary_pref = DietaryPreference(
        profile_id=profile.id,
        diet_type="omnivore",
        allergies=["dairy", "nuts"],
        intolerances=[],
        dislikes=[]
    )
    db_session.add(dietary_pref)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="muscle_gain"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find suggest_meal_substitution
    tools = agent.get_tools()
    substitution_tool = next(t for t in tools if t.name == "suggest_meal_substitution")
    
    # Call tool
    result = await substitution_tool.ainvoke({
        "meal_type": "lunch",
        "reason": "allergies"
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    
    # Verify dietary context includes allergies
    assert "dietary_context" in data["data"]
    assert "dairy" in data["data"]["dietary_context"]["allergies"]
    assert "nuts" in data["data"]["dietary_context"]["allergies"]


# ============================================================================
# Integration Tests - get_recipe_details Tool
# ============================================================================

@pytest.mark.integration
async def test_get_recipe_details_success(
    db_session: AsyncSession,
    test_user: User,
    sample_dishes: list,
    sample_ingredients: list
):
    """Test get_recipe_details retrieves recipe with ingredients."""
    # Get a dish from fixtures
    dish = sample_dishes[0]
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with dish name
    result = await recipe_tool.ainvoke({
        "dish_name": dish.name
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Assert recipe details are present
    assert data["data"]["dish_name"] == dish.name
    assert "ingredients" in data["data"]
    assert "nutritional_info" in data["data"]
    assert "dietary_tags" in data["data"]
    
    # Assert nutritional info
    assert data["data"]["nutritional_info"]["calories"] == float(dish.calories)
    assert data["data"]["nutritional_info"]["protein_g"] == float(dish.protein_g)


@pytest.mark.integration
async def test_get_recipe_details_not_found(
    db_session: AsyncSession,
    test_user: User
):
    """Test get_recipe_details handles missing dish gracefully."""
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="muscle_gain"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find get_recipe_details
    tools = agent.get_tools()
    recipe_tool = next(t for t in tools if t.name == "get_recipe_details")
    
    # Call tool with non-existent dish
    result = await recipe_tool.ainvoke({
        "dish_name": "NonExistentDish12345"
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "not found" in data["error"].lower()


# ============================================================================
# Integration Tests - calculate_nutrition Tool
# ============================================================================

@pytest.mark.integration
async def test_calculate_nutrition_success(
    db_session: AsyncSession,
    test_user: User,
    sample_dishes: list
):
    """Test calculate_nutrition calculates macros correctly."""
    # Get a dish from fixtures
    dish = sample_dishes[0]
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find calculate_nutrition
    tools = agent.get_tools()
    nutrition_tool = next(t for t in tools if t.name == "calculate_nutrition")
    
    # Call tool
    result = await nutrition_tool.ainvoke({
        "dish_name": dish.name
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert success
    assert data["success"] is True
    assert "data" in data
    
    # Assert nutritional data is present
    assert "per_serving" in data["data"]
    assert "macro_percentages" in data["data"]
    assert "calories_from_macros" in data["data"]
    assert "per_100g" in data["data"]
    
    # Assert per_serving matches dish
    assert data["data"]["per_serving"]["calories"] == float(dish.calories)
    assert data["data"]["per_serving"]["protein_g"] == float(dish.protein_g)
    
    # Assert macro percentages sum to approximately 100%
    percentages = data["data"]["macro_percentages"]
    total_percent = (
        percentages["protein_percent"] +
        percentages["carbs_percent"] +
        percentages["fats_percent"]
    )
    assert 95 <= total_percent <= 105  # Allow small rounding differences


@pytest.mark.integration
async def test_calculate_nutrition_not_found(
    db_session: AsyncSession,
    test_user: User
):
    """Test calculate_nutrition handles missing dish gracefully."""
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="advanced",
        primary_goal="general_fitness"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Get tools and find calculate_nutrition
    tools = agent.get_tools()
    nutrition_tool = next(t for t in tools if t.name == "calculate_nutrition")
    
    # Call tool with non-existent dish
    result = await nutrition_tool.ainvoke({
        "dish_name": "FakeDish99999"
    })
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "not found" in data["error"].lower()


# ============================================================================
# Integration Tests - Agent Text Processing
# ============================================================================

@pytest.mark.integration
async def test_diet_planner_process_text(
    db_session: AsyncSession,
    test_user: User
):
    """Test DietPlannerAgent can process text queries."""
    # Create UserProfile
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="intermediate",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessGoal
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="fat_loss",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Call process_text
    response = await agent.process_text("What should I eat for breakfast?")
    
    # Assert response is AgentResponse
    assert isinstance(response, AgentResponse)
    
    # Assert content is non-empty
    assert response.content is not None
    assert len(response.content) > 0
    assert isinstance(response.content, str)
    
    # Assert agent_type is "diet"
    assert response.agent_type == "diet"
    
    # Assert metadata contains expected fields
    assert "mode" in response.metadata
    assert response.metadata["mode"] == "text"
    assert "user_id" in response.metadata
    assert response.metadata["user_id"] == str(test_user.id)


@pytest.mark.integration
async def test_diet_planner_process_voice(
    db_session: AsyncSession,
    test_user: User
):
    """Test DietPlannerAgent can process voice queries with concise output."""
    # Create UserProfile
    profile = UserProfile(
        user_id=test_user.id,
        fitness_level="beginner",
        is_locked=False
    )
    db_session.add(profile)
    await db_session.commit()
    
    # Create FitnessGoal
    fitness_goal = FitnessGoal(
        profile_id=profile.id,
        goal_type="muscle_gain",
        priority=1
    )
    db_session.add(fitness_goal)
    await db_session.commit()
    
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="beginner",
        primary_goal="muscle_gain"
    )
    
    # Create DietPlannerAgent
    agent = DietPlannerAgent(context=context, db_session=db_session)
    
    # Call process_voice
    response = await agent.process_voice("What's a good post-workout meal?")
    
    # Assert response is string
    assert isinstance(response, str)
    
    # Assert content is non-empty
    assert len(response) > 0
    assert response.strip() != ""
    
    # Assert response is reasonably concise (rough check)
    word_count = len(response.split())
    assert word_count < 150  # Should be under 150 words for voice


# ============================================================================
# Error Handling Tests
# ============================================================================

@pytest.mark.integration
async def test_diet_planner_tool_without_db_session(test_user: User):
    """Test tools handle missing database session gracefully."""
    # Create AgentContext
    context = AgentContext(
        user_id=str(test_user.id),
        fitness_level="intermediate",
        primary_goal="fat_loss"
    )
    
    # Create DietPlannerAgent without db_session
    agent = DietPlannerAgent(context=context, db_session=None)
    
    # Get tools
    tools = agent.get_tools()
    meal_plan_tool = next(t for t in tools if t.name == "get_current_meal_plan")
    
    # Call tool
    result = await meal_plan_tool.ainvoke({})
    
    # Parse JSON result
    data = json.loads(result)
    
    # Assert failure with error message
    assert data["success"] is False
    assert "error" in data
    assert "database" in data["error"].lower()
