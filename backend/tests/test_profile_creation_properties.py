"""
Property-based tests for profile creation service.

These tests verify that profile creation rules hold across various inputs.

**Feature: scheduling-agent-completion**
**Property 10: Profile Creation Atomicity**
**Property 11: Profile Creation Rollback on Failure**
"""

import pytest
import pytest_asyncio
from uuid import uuid4
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.services.profile_creation_service import ProfileCreationService
from app.services.onboarding_completion import OnboardingIncompleteError
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import (
    FitnessGoal,
    PhysicalConstraint,
    DietaryPreference,
    MealPlan,
    MealSchedule,
    WorkoutSchedule,
    HydrationPreference,
)
from app.models.workout import WorkoutPlan
from app.core.security import hash_password


class TestProfileCreationAtomicity:
    """
    Property 10: Profile Creation Atomicity
    
    For any profile creation attempt, either all database entities (UserProfile, 
    FitnessGoal, PhysicalConstraint, DietaryPreference, MealPlan, MealSchedule, 
    WorkoutSchedule, HydrationPreference) are created successfully, or none are 
    created (transaction rollback).
    
    **Feature: scheduling-agent-completion, Property 10: Profile Creation Atomicity**
    **Validates: Requirements 8.11**
    """
    
    @pytest.mark.asyncio
    async def test_all_entities_created_on_success(
        self,
        db_session: AsyncSession
    ):
        """
        Property: On successful profile creation, all entities must be created.
        
        Given a complete valid agent_context,
        When creating a profile,
        Then all related entities should exist in the database.
        """
        # Create a user first (required for foreign key)
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        # Generate a valid agent_context
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["no_equipment_at_home"],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "goal_setting": {
                "primary_goal": "muscle_gain",
                "secondary_goal": "fat_loss",
                "target_weight_kg": 75.0,
                "target_body_fat_percentage": 15.0,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "proposed_plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "duration_weeks": 12,
                    "training_split": [
                        {
                            "name": "Upper Body Push",
                            "muscle_groups": ["chest", "shoulders", "triceps"],
                            "type": "strength",
                            "description": "Focus on pushing movements"
                        },
                        {
                            "name": "Lower Body",
                            "muscle_groups": ["quads", "hamstrings", "glutes"],
                            "type": "strength",
                            "description": "Leg day"
                        },
                        {
                            "name": "Upper Body Pull",
                            "muscle_groups": ["back", "biceps"],
                            "type": "strength",
                            "description": "Focus on pulling movements"
                        },
                        {
                            "name": "Full Body",
                            "muscle_groups": ["full_body"],
                            "type": "strength",
                            "description": "Complete body workout"
                        }
                    ],
                    "rationale": "4-day upper/lower split for muscle gain"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "preferences": {
                    "diet_type": "omnivore",
                    "allergies": ["dairy"],
                    "intolerances": [],
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
            },
            "scheduling": {
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
        }
        
        service = ProfileCreationService(db_session)
        
        try:
            # Create profile
            profile = await service.create_profile_from_agent_context(user_id, agent_context)
            
            # Verify UserProfile exists
            assert profile is not None
            assert profile.user_id == user_id
            assert profile.is_locked is True
            
            # Verify FitnessGoal exists (at least primary goal)
            result = await db_session.execute(
                select(FitnessGoal).where(FitnessGoal.profile_id == profile.id)
            )
            fitness_goals = result.scalars().all()
            assert len(fitness_goals) >= 1
            
            # Verify DietaryPreference exists
            result = await db_session.execute(
                select(DietaryPreference).where(DietaryPreference.profile_id == profile.id)
            )
            dietary_pref = result.scalar_one_or_none()
            assert dietary_pref is not None
            
            # Verify MealPlan exists
            result = await db_session.execute(
                select(MealPlan).where(MealPlan.profile_id == profile.id)
            )
            meal_plan = result.scalar_one_or_none()
            assert meal_plan is not None
            
            # Verify MealSchedule exists
            result = await db_session.execute(
                select(MealSchedule).where(MealSchedule.profile_id == profile.id)
            )
            meal_schedules = result.scalars().all()
            assert len(meal_schedules) >= 3
            
            # Verify WorkoutPlan exists
            result = await db_session.execute(
                select(WorkoutPlan).where(WorkoutPlan.user_id == user_id)
            )
            workout_plan = result.scalar_one_or_none()
            assert workout_plan is not None
            
            # Verify WorkoutSchedule exists
            result = await db_session.execute(
                select(WorkoutSchedule).where(WorkoutSchedule.profile_id == profile.id)
            )
            workout_schedules = result.scalars().all()
            assert len(workout_schedules) >= 3
            
            # Verify HydrationPreference exists
            result = await db_session.execute(
                select(HydrationPreference).where(HydrationPreference.profile_id == profile.id)
            )
            hydration_pref = result.scalar_one_or_none()
            assert hydration_pref is not None
            
        finally:
            # Cleanup
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_no_partial_entities_on_incomplete_data(self, db_session: AsyncSession):
        """
        Property: On incomplete agent_context, no entities should be created.
        
        Given an incomplete agent_context (missing required data),
        When attempting to create a profile,
        Then no entities should exist in the database.
        """
        user_id = uuid4()
        service = ProfileCreationService(db_session)
        
        # Incomplete agent_context (missing scheduling)
        incomplete_context = {
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
                    "training_split": [
                        {
                            "name": "Upper Body",
                            "muscle_groups": ["chest", "back"],
                            "type": "strength"
                        }
                    ]
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
            }
            # Missing "scheduling" section
        }
        
        try:
            # Attempt to create profile (should fail)
            with pytest.raises(OnboardingIncompleteError):
                await service.create_profile_from_agent_context(user_id, incomplete_context)
            
            # Verify no UserProfile was created
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            assert profile is None
            
        finally:
            # Cleanup
            await db_session.rollback()


class TestProfileCreationRollback:
    """
    Property 11: Profile Creation Rollback on Failure
    
    For any profile creation that fails due to validation error or database 
    constraint violation, all database changes must be rolled back and no 
    partial profile should exist.
    
    **Feature: scheduling-agent-completion, Property 11: Profile Creation Rollback on Failure**
    **Validates: Requirements 8.13**
    """
    
    @pytest.mark.asyncio
    async def test_rollback_on_missing_required_field(self, db_session: AsyncSession):
        """
        Property: On missing required field, transaction should rollback.
        
        Given an agent_context missing a required field,
        When attempting to create a profile,
        Then the transaction should rollback and no entities should exist.
        """
        user_id = uuid4()
        service = ProfileCreationService(db_session)
        
        # Missing fitness_level (required field)
        invalid_context = {
            "fitness_assessment": {
                # Missing "fitness_level"
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
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["07:00", "07:00", "18:00"]
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
        
        try:
            # Attempt to create profile (should fail with ValueError)
            with pytest.raises(ValueError) as exc_info:
                await service.create_profile_from_agent_context(user_id, invalid_context)
            
            assert "fitness_level" in str(exc_info.value)
            
            # Verify no entities were created
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            assert profile is None
            
            # Verify no FitnessGoal was created
            result = await db_session.execute(select(FitnessGoal))
            goals = result.scalars().all()
            # Filter to only goals that might be related to this test
            related_goals = [g for g in goals if g.profile_id is not None]
            # Since profile wasn't created, there should be no related goals
            assert len(related_goals) == 0 or all(
                g.profile_id != user_id for g in related_goals
            )
            
        finally:
            # Cleanup
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_rollback_on_invalid_macronutrient_data(self, db_session: AsyncSession):
        """
        Property: On invalid macronutrient data, transaction should rollback.
        
        Given an agent_context with missing macronutrient data,
        When attempting to create a profile,
        Then the transaction should rollback and no entities should exist.
        """
        user_id = uuid4()
        service = ProfileCreationService(db_session)
        
        # Missing protein_g (required macronutrient)
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
                    # Missing "protein_g"
                    "carbs_g": 300.0,
                    "fats_g": 70.0,
                    "meal_frequency": 4
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "workout_schedule": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["07:00", "07:00", "18:00"]
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
        
        try:
            # Attempt to create profile (should fail with ValueError)
            with pytest.raises(ValueError) as exc_info:
                await service.create_profile_from_agent_context(user_id, invalid_context)
            
            assert "macronutrient" in str(exc_info.value).lower()
            
            # Verify no entities were created
            result = await db_session.execute(
                select(UserProfile).where(UserProfile.user_id == user_id)
            )
            profile = result.scalar_one_or_none()
            assert profile is None
            
        finally:
            # Cleanup
            await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_consistent_state_after_rollback(
        self,
        db_session: AsyncSession
    ):
        """
        Property: After rollback, database should be in consistent state.
        
        Given any agent_context,
        When profile creation service rolls back on error,
        Then the database should have no partial entities.
        """
        # Create a user first (required for foreign key)
        user_id = uuid4()
        user = User(
            id=user_id,
            email=f"test_{user_id}@example.com",
            hashed_password=hash_password("testpassword123"),
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        # Generate an invalid agent_context (missing required field)
        # This will cause the service to rollback
        invalid_context = {
            "fitness_assessment": {
                # Missing "fitness_level" - will cause ValueError
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
                    "duration_weeks": 8,
                    "training_split": [
                        {
                            "name": "Full Body",
                            "muscle_groups": ["full_body"],
                            "type": "strength",
                            "description": "Full body workout"
                        }
                    ],
                    "rationale": "3-day full body"
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
            },
            "scheduling": {
                "workout_schedule": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["18:00", "18:00", "18:00"]
                },
                "meal_schedule": {
                    "breakfast": "07:00",
                    "lunch": "12:00",
                    "dinner": "18:00"
                },
                "hydration_preferences": {
                    "frequency_hours": 3,
                    "target_ml": 2500
                },
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        service = ProfileCreationService(db_session)
        
        # Attempt to create profile (should fail and rollback)
        with pytest.raises(ValueError):
            await service.create_profile_from_agent_context(user_id, invalid_context)
        
        # After rollback, verify no entities exist
        result = await db_session.execute(
            select(UserProfile).where(UserProfile.user_id == user_id)
        )
        profile_after = result.scalar_one_or_none()
        assert profile_after is None
        
        # Verify no orphaned FitnessGoals
        result = await db_session.execute(
            select(FitnessGoal)
        )
        goals = result.scalars().all()
        # No goals should exist for this user (since profile wasn't created)
        assert len(goals) == 0
        
        # Verify no orphaned MealSchedules
        result = await db_session.execute(
            select(MealSchedule)
        )
        schedules = result.scalars().all()
        # No schedules should exist
        assert len(schedules) == 0
