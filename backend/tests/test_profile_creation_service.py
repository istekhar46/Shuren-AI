"""
Unit tests for profile creation service.

These tests verify the ProfileCreationService methods work correctly
with various input scenarios including complete data, missing optional data,
and error conditions.

**Feature: scheduling-agent-completion**
"""

import pytest
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
    DietaryPreference,
    MealPlan,
)
from app.core.security import hash_password


class TestDataExtractionMethods:
    """Test data extraction helper methods."""
    
    @pytest.mark.asyncio
    async def test_extract_fitness_data_complete(self, db_session: AsyncSession):
        """Test extracting complete fitness data."""
        service = ProfileCreationService(db_session)
        
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["knee_injury", "no_equipment"],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_fitness_data(agent_context)
        
        assert result["fitness_level"] == "intermediate"
        assert result["limitations"] == ["knee_injury", "no_equipment"]
    
    @pytest.mark.asyncio
    async def test_extract_fitness_data_no_limitations(self, db_session: AsyncSession):
        """Test extracting fitness data with no limitations."""
        service = ProfileCreationService(db_session)
        
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": [],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_fitness_data(agent_context)
        
        assert result["fitness_level"] == "beginner"
        assert result["limitations"] == []
    
    @pytest.mark.asyncio
    async def test_extract_fitness_data_missing_fitness_level(self, db_session: AsyncSession):
        """Test extracting fitness data with missing fitness_level raises ValueError."""
        service = ProfileCreationService(db_session)
        
        agent_context = {
            "fitness_assessment": {
                "limitations": [],
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            service._extract_fitness_data(agent_context)
        
        assert "fitness_level" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_extract_goal_data_complete(self, db_session: AsyncSession):
        """Test extracting complete goal data with all optional fields from fitness_assessment."""
        service = ProfileCreationService(db_session)
        
        # Goals are now in fitness_assessment (Step 1) in the 4-step flow
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "primary_goal": "muscle_gain",
                "secondary_goal": "fat_loss",
                "target_weight_kg": 75.0,
                "target_body_fat_percentage": 15.0,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_goal_data(agent_context)
        
        assert result["primary_goal"] == "muscle_gain"
        assert result["secondary_goal"] == "fat_loss"
        assert result["target_weight_kg"] == 75.0
        assert result["target_body_fat_percentage"] == 15.0
    
    @pytest.mark.asyncio
    async def test_extract_goal_data_minimal(self, db_session: AsyncSession):
        """Test extracting goal data with only required fields from fitness_assessment."""
        service = ProfileCreationService(db_session)
        
        # Goals are now in fitness_assessment (Step 1) in the 4-step flow
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "primary_goal": "general_fitness",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_goal_data(agent_context)
        
        assert result["primary_goal"] == "general_fitness"
        assert result["secondary_goal"] is None
        assert result["target_weight_kg"] is None
        assert result["target_body_fat_percentage"] is None
    
    @pytest.mark.asyncio
    async def test_extract_workout_data_complete(self, db_session: AsyncSession):
        """Test extracting complete workout data from new structure (plan + schedule in workout_planning)."""
        service = ProfileCreationService(db_session)
        
        # New 4-step structure: plan and schedule both in workout_planning
        agent_context = {
            "workout_planning": {
                "plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "duration_weeks": 12,
                    "training_split": [
                        {
                            "name": "Upper Body",
                            "muscle_groups": ["chest", "back"],
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
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_workout_data(agent_context)
        
        assert result["frequency"] == 4
        assert result["duration_minutes"] == 60
        assert result["duration_weeks"] == 12
        assert len(result["training_split"]) == 1
        assert result["rationale"] == "4-day split for muscle gain"
    
    @pytest.mark.asyncio
    async def test_extract_diet_data_complete(self, db_session: AsyncSession):
        """Test extracting complete diet data from new structure (preferences + plan + schedule in diet_planning)."""
        service = ProfileCreationService(db_session)
        
        # New 4-step structure: preferences, plan, and schedule all in diet_planning
        agent_context = {
            "diet_planning": {
                "diet_type": "vegetarian",
                "allergies": ["dairy", "eggs"],
                "intolerances": ["lactose"],
                "dislikes": ["mushrooms"],
                "plan": {
                    "daily_calories": 2500,
                    "protein_g": 150.0,
                    "carbs_g": 300.0,
                    "fats_g": 70.0,
                    "meal_frequency": 4
                },
                "schedule": {
                    "breakfast": "08:00",
                    "lunch": "13:00",
                    "snack": "16:00",
                    "dinner": "19:00"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_diet_data(agent_context)
        
        assert result["diet_type"] == "vegetarian"
        assert result["allergies"] == ["dairy", "eggs"]
        assert result["intolerances"] == ["lactose"]
        assert result["dislikes"] == ["mushrooms"]
        assert result["meal_plan"]["daily_calories"] == 2500
        assert result["meal_plan"]["protein_g"] == 150.0
    
    @pytest.mark.asyncio
    async def test_extract_schedule_data_complete(self, db_session: AsyncSession):
        """Test extracting complete schedule data from new 4-step structure."""
        service = ProfileCreationService(db_session)
        
        # New 4-step structure:
        # - Workout schedule in workout_planning
        # - Meal schedule in diet_planning
        # - Hydration in scheduling
        agent_context = {
            "workout_planning": {
                "schedule": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["07:00", "07:00", "18:00"]
                }
            },
            "diet_planning": {
                "schedule": {
                    "breakfast": "08:00",
                    "lunch": "13:00",
                    "dinner": "19:00"
                }
            },
            "scheduling": {
                "daily_water_target_ml": 3000,
                "reminder_frequency_minutes": 120,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        result = service._extract_schedule_data(agent_context)
        
        assert result["workout_schedule"]["days"] == ["Monday", "Wednesday", "Friday"]
        assert result["meal_schedule"]["breakfast"] == "08:00"
        assert result["hydration_preferences"]["target_ml"] == 3000
        assert result["hydration_preferences"]["frequency_hours"] == 2


class TestEntityCreationMethods:
    """Test entity creation helper methods."""
    
    @pytest.mark.asyncio
    async def test_create_profile_entity(self, db_session: AsyncSession):
        """Test creating UserProfile entity."""
        service = ProfileCreationService(db_session)
        user_id = uuid4()
        
        profile = service._create_profile_entity(user_id, "intermediate")
        
        assert profile.user_id == user_id
        assert profile.fitness_level == "intermediate"
        assert profile.is_locked is True
    
    @pytest.mark.asyncio
    async def test_create_fitness_goals_primary_only(self, db_session: AsyncSession):
        """Test creating fitness goals with primary goal only."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        goal_data = {
            "primary_goal": "fat_loss",
            "secondary_goal": None,
            "target_weight_kg": None,
            "target_body_fat_percentage": None
        }
        
        goals = service._create_fitness_goals(profile_id, goal_data)
        
        assert len(goals) == 1
        assert goals[0].goal_type == "fat_loss"
        assert goals[0].priority == 1
    
    @pytest.mark.asyncio
    async def test_create_fitness_goals_with_secondary(self, db_session: AsyncSession):
        """Test creating fitness goals with both primary and secondary."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        goal_data = {
            "primary_goal": "muscle_gain",
            "secondary_goal": "fat_loss",
            "target_weight_kg": 80.0,
            "target_body_fat_percentage": 12.0
        }
        
        goals = service._create_fitness_goals(profile_id, goal_data)
        
        assert len(goals) == 2
        assert goals[0].goal_type == "muscle_gain"
        assert goals[0].priority == 1
        assert goals[0].target_weight_kg == 80.0
        assert goals[1].goal_type == "fat_loss"
        assert goals[1].priority == 2
    
    @pytest.mark.asyncio
    async def test_create_physical_constraints_empty(self, db_session: AsyncSession):
        """Test creating physical constraints with empty list."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        constraints = service._create_physical_constraints(profile_id, [])
        
        assert len(constraints) == 0
    
    @pytest.mark.asyncio
    async def test_create_physical_constraints_multiple(self, db_session: AsyncSession):
        """Test creating multiple physical constraints."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        limitations = ["knee_injury", "no_equipment", "back_pain"]
        constraints = service._create_physical_constraints(profile_id, limitations)
        
        assert len(constraints) == 3
        assert all(c.constraint_type == "limitation" for c in constraints)
        assert constraints[0].description == "knee_injury"
    
    @pytest.mark.asyncio
    async def test_create_dietary_preference(self, db_session: AsyncSession):
        """Test creating dietary preference entity."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        diet_data = {
            "diet_type": "vegan",
            "allergies": ["nuts"],
            "intolerances": ["gluten"],
            "dislikes": ["tofu"]
        }
        
        pref = service._create_dietary_preference(profile_id, diet_data)
        
        assert pref.diet_type == "vegan"
        assert pref.allergies == ["nuts"]
        assert pref.intolerances == ["gluten"]
        assert pref.dislikes == ["tofu"]
    
    @pytest.mark.asyncio
    async def test_create_meal_plan(self, db_session: AsyncSession):
        """Test creating meal plan entity."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        meal_plan_data = {
            "daily_calories": 2800,
            "protein_g": 175.0,
            "carbs_g": 350.0,
            "fats_g": 78.0
        }
        
        meal_plan = service._create_meal_plan(profile_id, meal_plan_data)
        
        assert meal_plan.daily_calorie_target == 2800
        assert meal_plan.protein_grams == 175.0
        assert meal_plan.carbs_grams == 350.0
        assert meal_plan.fats_grams == 78.0
    
    @pytest.mark.asyncio
    async def test_create_meal_schedules(self, db_session: AsyncSession):
        """Test creating meal schedule entities."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        meal_schedule_data = {
            "breakfast": "08:00",
            "lunch": "13:00",
            "snack": "16:00",
            "dinner": "19:00"
        }
        
        schedules = service._create_meal_schedules(profile_id, meal_schedule_data)
        
        assert len(schedules) == 4
        assert schedules[0].meal_name == "breakfast"
        assert schedules[0].enable_notifications is True
    
    @pytest.mark.asyncio
    async def test_create_workout_schedules(self, db_session: AsyncSession):
        """Test creating workout schedule entities."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        workout_schedule_data = {
            "days": ["Monday", "Wednesday", "Friday"],
            "times": ["07:00", "07:00", "18:00"]
        }
        
        schedules = service._create_workout_schedules(profile_id, workout_schedule_data)
        
        assert len(schedules) == 3
        assert schedules[0].day_of_week == 0  # Monday
        assert schedules[1].day_of_week == 2  # Wednesday
        assert schedules[2].day_of_week == 4  # Friday
        assert schedules[0].enable_notifications is True
    
    @pytest.mark.asyncio
    async def test_create_hydration_preference(self, db_session: AsyncSession):
        """Test creating hydration preference entity."""
        service = ProfileCreationService(db_session)
        profile_id = uuid4()
        
        hydration_data = {
            "frequency_hours": 2,
            "target_ml": 3000
        }
        
        pref = service._create_hydration_preference(profile_id, hydration_data)
        
        assert pref.daily_water_target_ml == 3000
        assert pref.reminder_frequency_minutes == 120  # 2 hours * 60
        assert pref.enable_notifications is True


class TestCompleteProfileCreation:
    """Test complete profile creation flow."""
    
    @pytest.mark.asyncio
    async def test_create_profile_with_complete_data(self, db_session: AsyncSession):
        """Test creating profile with complete valid data."""
        # Create user first
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
        
        # Complete agent_context for 4-step flow
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": ["no_equipment"],
                "primary_goal": "muscle_gain",
                "secondary_goal": "fat_loss",
                "target_weight_kg": 75.0,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "duration_weeks": 12,
                    "training_split": [
                        {
                            "name": "Upper Body",
                            "muscle_groups": ["chest", "back"],
                            "type": "strength"
                        }
                    ],
                    "rationale": "4-day split"
                },
                "schedule": {
                    "days": ["Monday", "Wednesday", "Friday", "Saturday"],
                    "times": ["07:00", "07:00", "18:00", "09:00"]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": [],
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
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "daily_water_target_ml": 3000,
                "reminder_frequency_minutes": 120,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        service = ProfileCreationService(db_session)
        profile = await service.create_profile_from_agent_context(user_id, agent_context)
        
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.fitness_level == "intermediate"
        assert profile.is_locked is True
        
        # Cleanup
        await db_session.rollback()
    
    @pytest.mark.asyncio
    async def test_create_profile_with_minimal_optional_data(self, db_session: AsyncSession):
        """Test creating profile with minimal optional data."""
        # Create user first
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
        
        # Minimal agent_context for 4-step flow (no secondary goal, no limitations, etc.)
        agent_context = {
            "fitness_assessment": {
                "fitness_level": "beginner",
                "limitations": [],
                "primary_goal": "general_fitness",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 3,
                    "duration_minutes": 45,
                    "training_split": [
                        {
                            "name": "Full Body",
                            "muscle_groups": ["full_body"],
                            "type": "strength"
                        }
                    ]
                },
                "schedule": {
                    "days": ["Monday", "Wednesday", "Friday"],
                    "times": ["18:00", "18:00", "18:00"]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": [],
                "plan": {
                    "daily_calories": 2000,
                    "protein_g": 120.0,
                    "carbs_g": 250.0,
                    "fats_g": 60.0,
                    "meal_frequency": 3
                },
                "schedule": {
                    "breakfast": "07:00",
                    "lunch": "12:00",
                    "dinner": "18:00"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "daily_water_target_ml": 2500,
                "reminder_frequency_minutes": 180,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        service = ProfileCreationService(db_session)
        profile = await service.create_profile_from_agent_context(user_id, agent_context)
        
        assert profile is not None
        assert profile.user_id == user_id
        assert profile.fitness_level == "beginner"
        
        # Verify only one fitness goal created (no secondary)
        result = await db_session.execute(
            select(FitnessGoal).where(FitnessGoal.profile_id == profile.id)
        )
        goals = result.scalars().all()
        assert len(goals) == 1
        
        # Cleanup
        await db_session.rollback()


class TestErrorHandling:
    """Test error handling in profile creation."""
    
    @pytest.mark.asyncio
    async def test_missing_required_field_raises_value_error(self, db_session: AsyncSession):
        """Test that missing required field raises ValueError."""
        user_id = uuid4()
        service = ProfileCreationService(db_session)
        
        # Missing fitness_level in 4-step structure
        invalid_context = {
            "fitness_assessment": {
                "limitations": [],
                "primary_goal": "muscle_gain",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "training_split": [{"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}]
                },
                "schedule": {
                    "days": ["Monday"],
                    "times": ["07:00"]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": [],
                "plan": {
                    "daily_calories": 2500,
                    "protein_g": 150.0,
                    "carbs_g": 300.0,
                    "fats_g": 70.0,
                    "meal_frequency": 4
                },
                "schedule": {
                    "breakfast": "08:00"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "scheduling": {
                "daily_water_target_ml": 3000,
                "reminder_frequency_minutes": 120,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
        }
        
        with pytest.raises(ValueError) as exc_info:
            await service.create_profile_from_agent_context(user_id, invalid_context)
        
        assert "fitness_level" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_incomplete_onboarding_raises_error(self, db_session: AsyncSession):
        """Test that incomplete onboarding raises OnboardingIncompleteError."""
        user_id = uuid4()
        service = ProfileCreationService(db_session)
        
        # Missing scheduling section in 4-step structure
        incomplete_context = {
            "fitness_assessment": {
                "fitness_level": "intermediate",
                "limitations": [],
                "primary_goal": "muscle_gain",
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "workout_planning": {
                "plan": {
                    "frequency": 4,
                    "duration_minutes": 60,
                    "training_split": [{"name": "Day 1", "muscle_groups": ["chest"], "type": "strength"}]
                },
                "schedule": {
                    "days": ["Monday"],
                    "times": ["07:00"]
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            },
            "diet_planning": {
                "diet_type": "omnivore",
                "allergies": [],
                "intolerances": [],
                "dislikes": [],
                "plan": {
                    "daily_calories": 2500,
                    "protein_g": 150.0,
                    "carbs_g": 300.0,
                    "fats_g": 70.0,
                    "meal_frequency": 4
                },
                "schedule": {
                    "breakfast": "08:00"
                },
                "user_approved": True,
                "completed_at": datetime.utcnow().isoformat() + "Z"
            }
            # Missing "scheduling" section
        }
        
        with pytest.raises(OnboardingIncompleteError):
            await service.create_profile_from_agent_context(user_id, incomplete_context)
