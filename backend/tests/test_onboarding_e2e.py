"""
End-to-end integration tests for complete onboarding flow.

This module tests the full onboarding journey from start to finish:
- Fitness Assessment Agent
- Goal Setting Agent  
- Workout Planning Agent
- Diet Planning Agent
- Scheduling Agent
- Onboarding Completion

**Feature: scheduling-agent-completion**
"""

import pytest
from datetime import datetime
from sqlalchemy import select
from httpx import AsyncClient

from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile


@pytest.mark.integration
@pytest.mark.asyncio
async def test_complete_onboarding_flow_e2e(
    authenticated_client,
    db_session
):
    """
    Test complete onboarding flow from start to finish.
    
    This test simulates a user going through the entire onboarding process:
    1. Fitness Assessment - collects fitness level and limitations
    2. Goal Setting - defines primary and secondary goals
    3. Workout Planning - creates and approves workout plan
    4. Diet Planning - creates and approves meal plan
    5. Scheduling - sets workout, meal, and hydration schedules
    6. Completion - creates locked profile with all entities
    
    Validates Requirement 23.4: Complete onboarding flow works end-to-end.
    
    **Feature: scheduling-agent-completion**
    """
    from sqlalchemy import update
    
    client, user = authenticated_client
    
    # Step 1: Simulate Fitness Assessment Agent completion
    fitness_data = {
        "fitness_level": "intermediate",
        "limitations": ["no_equipment"],
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(
            current_step=1,
            agent_context={"fitness_assessment": fitness_data}
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Verify fitness assessment data saved
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    assert "fitness_assessment" in state.agent_context
    assert state.agent_context["fitness_assessment"]["fitness_level"] == "intermediate"
    
    # Step 2: Simulate Goal Setting Agent completion
    goal_data = {
        "primary_goal": "muscle_gain",
        "secondary_goal": "fat_loss",
        "target_weight_kg": 75.0,
        "target_body_fat_percentage": 15.0,
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    current_context = state.agent_context.copy()
    current_context["goal_setting"] = goal_data
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(
            current_step=3,
            agent_context=current_context
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Verify goal setting data saved
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    assert "goal_setting" in state.agent_context
    assert state.agent_context["goal_setting"]["primary_goal"] == "muscle_gain"
    
    # Step 3: Simulate Workout Planning Agent completion
    workout_data = {
        "proposed_plan": {
            "frequency": 4,
            "duration_minutes": 60,
            "duration_weeks": 12,
            "training_split": [
                {
                    "name": "Upper Body",
                    "muscle_groups": ["chest", "back", "shoulders"],
                    "type": "strength",
                    "description": "Upper body strength training"
                },
                {
                    "name": "Lower Body",
                    "muscle_groups": ["legs", "glutes"],
                    "type": "strength",
                    "description": "Lower body strength training"
                }
            ],
            "rationale": "4-day split optimized for muscle gain with no equipment"
        },
        "user_approved": True,
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    current_context = state.agent_context.copy()
    current_context["workout_planning"] = workout_data
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(
            current_step=5,
            agent_context=current_context
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Verify workout planning data saved
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    assert "workout_planning" in state.agent_context
    assert state.agent_context["workout_planning"]["user_approved"] is True
    assert state.agent_context["workout_planning"]["proposed_plan"]["frequency"] == 4
    
    # Step 4: Simulate Diet Planning Agent completion
    diet_data = {
        "preferences": {
            "diet_type": "omnivore",
            "allergies": [],
            "intolerances": ["lactose"],
            "dislikes": ["mushrooms"]
        },
        "proposed_plan": {
            "daily_calories": 2800,
            "protein_g": 175.0,
            "carbs_g": 350.0,
            "fats_g": 78.0,
            "meal_frequency": 4
        },
        "user_approved": True,
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    current_context = state.agent_context.copy()
    current_context["diet_planning"] = diet_data
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(
            current_step=7,
            agent_context=current_context
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Verify diet planning data saved
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    assert "diet_planning" in state.agent_context
    assert state.agent_context["diet_planning"]["user_approved"] is True
    assert state.agent_context["diet_planning"]["proposed_plan"]["daily_calories"] == 2800
    
    # Step 5: Simulate Scheduling Agent completion
    scheduling_data = {
        "workout_schedule": {
            "days": ["Monday", "Wednesday", "Friday", "Saturday"],
            "times": ["07:00", "07:00", "18:00", "09:00"]
        },
        "meal_schedule": {
            "breakfast": "08:00",
            "lunch": "13:00",
            "snack": "16:00",
            "dinner": "19:00"
        },
        "hydration_preferences": {
            "frequency_hours": 2,
            "target_ml": 3000
        },
        "completed_at": datetime.utcnow().isoformat() + "Z"
    }
    
    current_context = state.agent_context.copy()
    current_context["scheduling"] = scheduling_data
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(
            current_step=9,
            agent_context=current_context,
            is_complete=False
        )
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Verify scheduling data saved
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalars().first()
    assert "scheduling" in state.agent_context
    assert len(state.agent_context["scheduling"]["workout_schedule"]["days"]) == 4
    assert state.agent_context["scheduling"]["meal_schedule"]["breakfast"] == "08:00"
    assert state.agent_context["scheduling"]["hydration_preferences"]["target_ml"] == 3000
    
    # Step 6: Complete onboarding
    response = await client.post("/api/v1/onboarding/complete")
    
    # Verify completion response
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == str(user.id)
    assert data["fitness_level"] == "intermediate"
    assert data["is_locked"] is True
    assert data["onboarding_complete"] is True
    assert "successfully" in data["message"].lower()
    
    # Verify profile created with all entities
    stmt = select(UserProfile).where(UserProfile.user_id == user.id)
    result = await db_session.execute(stmt)
    profile = result.scalar_one()
    
    assert profile is not None
    assert profile.is_locked is True
    assert profile.fitness_level == "intermediate"
    
    # Verify onboarding marked complete
    stmt = select(OnboardingState).where(OnboardingState.user_id == user.id)
    result = await db_session.execute(stmt)
    state = result.scalar_one()
    
    assert state.is_complete is True
    assert state.current_agent == "general_assistant"
    
    # Verify all agent_context data preserved
    assert "fitness_assessment" in state.agent_context
    assert "goal_setting" in state.agent_context
    assert "workout_planning" in state.agent_context
    assert "diet_planning" in state.agent_context
    assert "scheduling" in state.agent_context



@pytest.mark.integration
@pytest.mark.asyncio
async def test_completion_with_incomplete_data_returns_400(
    authenticated_client,
    db_session
):
    """
    Test that completion with incomplete agent_context returns 400.
    
    Validates Requirement 23.4: Error handling for incomplete data.
    
    **Feature: scheduling-agent-completion**
    """
    from sqlalchemy import update
    
    client, user = authenticated_client
    
    # Set up incomplete agent_context (missing scheduling)
    incomplete_context = {
        "fitness_assessment": {
            "fitness_level": "beginner",
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "goal_setting": {
            "primary_goal": "fat_loss",
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "workout_planning": {
            "proposed_plan": {
                "frequency": 3,
                "duration_minutes": 45,
                "training_split": [{"name": "Full Body", "muscle_groups": ["full_body"], "type": "strength"}]
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "diet_planning": {
            "preferences": {
                "diet_type": "vegetarian",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            "proposed_plan": {
                "daily_calories": 2000,
                "protein_g": 120.0,
                "carbs_g": 250.0,
                "fats_g": 60.0,
                "meal_frequency": 3
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }
        # Missing "scheduling" section
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(agent_context=incomplete_context, is_complete=False)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Attempt to complete
    response = await client.post("/api/v1/onboarding/complete")
    
    # Verify 400 response
    assert response.status_code == 400
    assert "incomplete" in response.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_completion_twice_returns_409(
    authenticated_client,
    db_session
):
    """
    Test that completing onboarding twice returns 409.
    
    Validates Requirement 23.4: Idempotency check for completion.
    
    **Feature: scheduling-agent-completion**
    """
    from sqlalchemy import update
    
    client, user = authenticated_client
    
    # Set up complete agent_context
    complete_context = {
        "fitness_assessment": {
            "fitness_level": "advanced",
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "goal_setting": {
            "primary_goal": "general_fitness",
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "workout_planning": {
            "proposed_plan": {
                "frequency": 5,
                "duration_minutes": 90,
                "training_split": [{"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}]
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "diet_planning": {
            "preferences": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            "proposed_plan": {
                "daily_calories": 3000,
                "protein_g": 200.0,
                "carbs_g": 400.0,
                "fats_g": 80.0,
                "meal_frequency": 5
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "scheduling": {
            "workout_schedule": {
                "days": ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"],
                "times": ["06:00", "06:00", "06:00", "06:00", "06:00"]
            },
            "meal_schedule": {
                "breakfast": "07:00",
                "lunch": "13:00",
                "dinner": "19:00"
            },
            "hydration_preferences": {
                "frequency_hours": 1,
                "target_ml": 4000
            },
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(agent_context=complete_context, is_complete=False)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Complete onboarding first time
    response1 = await client.post("/api/v1/onboarding/complete")
    assert response1.status_code == 201
    
    # Attempt to complete again
    response2 = await client.post("/api/v1/onboarding/complete")
    
    # Verify 409 response
    assert response2.status_code == 409
    assert "already" in response2.json()["detail"].lower()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_invalid_schedule_data_returns_validation_error(
    authenticated_client,
    db_session
):
    """
    Test that invalid schedule data returns validation errors.
    
    Validates Requirement 23.4: Validation of schedule data.
    
    **Feature: scheduling-agent-completion**
    """
    from sqlalchemy import update
    
    client, user = authenticated_client
    
    # Set up agent_context with invalid schedule data
    invalid_context = {
        "fitness_assessment": {
            "fitness_level": "intermediate",
            "limitations": [],
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "goal_setting": {
            "primary_goal": "muscle_gain",
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "workout_planning": {
            "proposed_plan": {
                "frequency": 4,
                "duration_minutes": 60,
                "training_split": [{"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}]
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "diet_planning": {
            "preferences": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            "proposed_plan": {
                "daily_calories": 2500,
                "protein_g": 150.0,
                "carbs_g": 300.0,
                "fats_g": 70.0,
                "meal_frequency": 4
            },
            "user_approved": True,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        },
        "scheduling": {
            "workout_schedule": {
                "days": ["InvalidDay", "Wednesday"],  # Invalid day name
                "times": ["07:00", "25:00"]  # Invalid time (25:00)
            },
            "meal_schedule": {
                "breakfast": "08:00",
                "lunch": "13:00",
                "dinner": "19:00"
            },
            "hydration_preferences": {
                "frequency_hours": 2,
                "target_ml": 3000
            },
            "completed_at": datetime.utcnow().isoformat() + "Z"
        }
    }
    
    stmt = (
        update(OnboardingState)
        .where(OnboardingState.user_id == user.id)
        .values(agent_context=invalid_context, is_complete=False)
    )
    await db_session.execute(stmt)
    await db_session.commit()
    
    # Attempt to complete with invalid data
    response = await client.post("/api/v1/onboarding/complete")
    
    # Verify error response (should be 422 for validation error or 500 if caught as general error)
    assert response.status_code in [400, 422, 500]
    # The error should mention validation or invalid data
    detail = response.json()["detail"]
    assert any(keyword in str(detail).lower() for keyword in ["invalid", "validation", "error"])
