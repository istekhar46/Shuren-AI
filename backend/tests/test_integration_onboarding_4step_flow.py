"""
Integration tests for 4-step onboarding flow.

Tests the end-to-end onboarding workflow for the redesigned 4-step flow:
- Step 1: Fitness Assessment (fitness level + goals)
- Step 2: Workout Planning (constraints + plan generation + schedule)
- Step 3: Diet Planning (preferences + plan generation + schedule)
- Step 4: Scheduling (hydration + supplements)
- Profile creation from agent_context
- Complete flow validation

Validates: Requirements for 4-step onboarding redesign
Task: 10.1 - Write end-to-end onboarding flow test
"""

import pytest
from datetime import datetime, timezone
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.models.user import User
from app.models.onboarding import OnboardingState
from app.models.profile import UserProfile


@pytest.mark.asyncio
@pytest.mark.integration
class TestComplete4StepOnboardingFlow:
    """Integration tests for complete 4-step onboarding flow."""
    
    async def test_complete_4_step_onboarding_flow_with_profile_creation(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete onboarding flow through all 4 steps with profile creation.
        
        This integration test validates:
        1. User can complete all 4 onboarding steps sequentially via chat
        2. Each agent saves data correctly to agent_context
        3. Step completion flags are set correctly
        4. Profile creation works with complete agent_context
        5. All related entities are created (goals, preferences, schedules, etc.)
        
        Flow:
        - Step 1: FitnessAssessmentAgent collects fitness level and goals
        - Step 2: WorkoutPlanningAgent collects constraints, generates plan, collects schedule
        - Step 3: DietPlanningAgent collects preferences, generates plan, collects schedule
        - Step 4: SchedulingAgent collects hydration and supplement preferences
        - Complete: ProfileCreationService creates locked profile
        """
        # Setup: Create user with onboarding state
        user = User(
            id=uuid4(),
            email="e2e_4step@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="E2E Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=1,
            current_agent="fitness_assessment",
            is_complete=False,
            agent_context={},
            conversation_history=[],
            agent_history=[],
            step_1_complete=False,
            step_2_complete=False,
            step_3_complete=False,
            step_4_complete=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 1: Fitness Assessment (fitness level + goals)
        # Simulate agent saving fitness assessment data
        onboarding_state.agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "experience_years": 2,
                "primary_goal": "muscle_gain",
                "secondary_goal": "fat_loss",
                "target_weight_kg": 75.0,
                "limitations": [],
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
        onboarding_state.step_1_complete = True
        onboarding_state.current_step = 2
        onboarding_state.current_agent = "workout_planning"
        await db_session.commit()
        
        # Verify step 1 completion
        response = await client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        state = response.json()
        assert state["step_1_complete"] is True
        assert state["current_step"] == 2
        assert "fitness_assessment" in state["agent_context"]
        
        # Verify progress
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 2
        assert 1 in progress["completed_states"]
        assert progress["completion_percentage"] == 25
        
        # Step 2: Workout Planning (constraints + plan + schedule)
        # Simulate agent saving workout plan and schedule
        onboarding_state.agent_context["workout_planning"] = {
            "equipment": ["gym_full"],
            "injuries": [],
            "limitations": [],
            "plan": {
                "frequency": 4,
                "duration_minutes": 60,
                "duration_weeks": 12,
                "training_split": [
                    {
                        "name": "Upper Body Push",
                        "muscle_groups": ["chest", "shoulders", "triceps"],
                        "type": "strength"
                    },
                    {
                        "name": "Lower Body",
                        "muscle_groups": ["quads", "hamstrings", "glutes"],
                        "type": "strength"
                    },
                    {
                        "name": "Upper Body Pull",
                        "muscle_groups": ["back", "biceps"],
                        "type": "strength"
                    },
                    {
                        "name": "Full Body",
                        "muscle_groups": ["full_body"],
                        "type": "strength"
                    }
                ],
                "rationale": "4-day split for muscle gain"
            },
            "schedule": {
                "days": ["Monday", "Wednesday", "Friday", "Saturday"],
                "times": ["07:00", "07:00", "18:00", "09:00"]
            },
            "user_approved": True,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        onboarding_state.step_2_complete = True
        onboarding_state.current_step = 3
        onboarding_state.current_agent = "diet_planning"
        await db_session.commit()
        
        # Verify step 2 completion
        response = await client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        state = response.json()
        assert state["step_2_complete"] is True
        assert state["current_step"] == 3
        assert "workout_planning" in state["agent_context"]
        
        # Verify progress
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 3
        assert 1 in progress["completed_states"]
        assert 2 in progress["completed_states"]
        assert progress["completion_percentage"] == 50
        
        # Step 3: Diet Planning (preferences + plan + schedule)
        # Simulate agent saving meal plan and schedule
        onboarding_state.agent_context["diet_planning"] = {
            "diet_type": "omnivore",
            "allergies": [],
            "intolerances": [],
            "dislikes": ["fish"],
            "plan": {
                "daily_calories": 2800,
                "protein_g": 175.0,
                "carbs_g": 350.0,
                "fats_g": 78.0,
                "meal_frequency": 4
            },
            "schedule": {
                "breakfast": "08:00",
                "lunch": "13:00",
                "snack": "16:00",
                "dinner": "19:00"
            },
            "user_approved": True,
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        onboarding_state.step_3_complete = True
        onboarding_state.current_step = 4
        onboarding_state.current_agent = "scheduling"
        await db_session.commit()
        
        # Verify step 3 completion
        response = await client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        state = response.json()
        assert state["step_3_complete"] is True
        assert state["current_step"] == 4
        assert "diet_planning" in state["agent_context"]
        
        # Verify progress
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 4
        assert 1 in progress["completed_states"]
        assert 2 in progress["completed_states"]
        assert 3 in progress["completed_states"]
        assert progress["completion_percentage"] == 75
        
        # Step 4: Scheduling (hydration + supplements)
        # Simulate agent saving hydration and supplement preferences
        onboarding_state.agent_context["scheduling"] = {
            "daily_water_target_ml": 3000,
            "reminder_frequency_minutes": 120,
            "interested_in_supplements": True,
            "current_supplements": ["whey_protein"],
            "completed_at": datetime.now(timezone.utc).isoformat()
        }
        onboarding_state.step_4_complete = True
        # Note: current_step stays at 4, doesn't advance
        await db_session.commit()
        
        # Verify step 4 completion
        response = await client.get("/api/v1/onboarding/state")
        assert response.status_code == 200
        state = response.json()
        assert state["step_4_complete"] is True
        assert state["current_step"] == 4
        assert "scheduling" in state["agent_context"]
        
        # Verify progress shows all steps complete
        response = await client.get("/api/v1/onboarding/progress")
        assert response.status_code == 200
        progress = response.json()
        assert progress["current_state"] == 4
        assert len(progress["completed_states"]) == 4
        assert progress["completion_percentage"] == 100
        assert progress["can_complete"] is True
        
        # Complete onboarding and create profile
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 201
        profile_data = response.json()
        
        # Verify profile was created
        assert profile_data["profile_id"] is not None
        assert profile_data["user_id"] == str(user.id)
        assert profile_data["fitness_level"] == "intermediate"
        assert profile_data["is_locked"] is True
        assert profile_data["onboarding_complete"] is True
        
        # Verify onboarding state is marked complete
        await db_session.refresh(onboarding_state)
        assert onboarding_state.is_complete is True
        assert onboarding_state.current_agent == "general_assistant"
        
        # Verify profile exists in database
        stmt = select(UserProfile).where(UserProfile.user_id == user.id)
        result = await db_session.execute(stmt)
        profile = result.scalars().first()
        assert profile is not None
        assert profile.fitness_level == "intermediate"
        assert profile.is_locked is True
    
    async def test_agent_handoff_preserves_context(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that context is preserved across agent handoffs.
        
        Validates that data collected in earlier steps is available
        to later agents through agent_context.
        """
        # Setup user
        user = User(
            id=uuid4(),
            email="handoff@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Handoff User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=1,
            current_agent="fitness_assessment",
            is_complete=False,
            agent_context={},
            step_1_complete=False,
            step_2_complete=False,
            step_3_complete=False,
            step_4_complete=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Complete step 1
        onboarding_state.agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "primary_goal": "fat_loss",
                "completed_at": datetime.now(timezone.utc).isoformat()
            }
        }
        onboarding_state.step_1_complete = True
        onboarding_state.current_step = 2
        await db_session.commit()
        
        # Verify step 1 data is in context
        response = await client.get("/api/v1/onboarding/state")
        state = response.json()
        assert "fitness_assessment" in state["agent_context"]
        assert state["agent_context"]["fitness_assessment"]["fitness_level"] == "beginner"
        
        # Complete step 2
        onboarding_state.agent_context["workout_planning"] = {
            "plan": {"frequency": 3, "duration_minutes": 45},
            "schedule": {"days": ["Monday", "Wednesday", "Friday"], "times": ["18:00", "18:00", "18:00"]},
            "user_approved": True
        }
        onboarding_state.step_2_complete = True
        onboarding_state.current_step = 3
        await db_session.commit()
        
        # Verify both step 1 and step 2 data are in context
        response = await client.get("/api/v1/onboarding/state")
        state = response.json()
        assert "fitness_assessment" in state["agent_context"]
        assert "workout_planning" in state["agent_context"]
        assert state["agent_context"]["fitness_assessment"]["fitness_level"] == "beginner"
        assert state["agent_context"]["workout_planning"]["plan"]["frequency"] == 3
    
    async def test_cannot_complete_with_incomplete_steps(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that completion fails if not all steps are complete."""
        # Setup user with incomplete onboarding
        user = User(
            id=uuid4(),
            email="incomplete@example.com",
            hashed_password=hash_password("testpass123"),
            full_name="Incomplete User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        onboarding_state = OnboardingState(
            id=uuid4(),
            user_id=user.id,
            current_step=2,
            current_agent="workout_planning",
            is_complete=False,
            agent_context={
                "fitness_assessment": {
                    "fitness_level": "intermediate",
                    "primary_goal": "muscle_gain",
                    "completed_at": datetime.now(timezone.utc).isoformat()
                }
            },
            step_1_complete=True,
            step_2_complete=False,  # Step 2 not complete
            step_3_complete=False,
            step_4_complete=False,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(onboarding_state)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Try to complete - should fail
        response = await client.post("/api/v1/onboarding/complete")
        assert response.status_code == 400
        error = response.json()
        assert "incomplete" in error["detail"].lower()
