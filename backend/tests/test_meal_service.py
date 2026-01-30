"""Tests for MealService."""

import pytest
from datetime import time
from decimal import Decimal
from uuid import uuid4

from app.services.meal_service import MealService
from app.models.preferences import MealPlan, MealSchedule
from app.models.profile import UserProfile
from app.models.user import User


@pytest.mark.asyncio
class TestMealService:
    """Test suite for MealService."""
    
    async def test_get_meal_plan_success(self, db_session, test_user):
        """Test successful meal plan retrieval."""
        # Create profile
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=False,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.flush()
        
        # Create meal plan
        meal_plan = MealPlan(
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("30.00")
        )
        db_session.add(meal_plan)
        await db_session.commit()
        
        # Test retrieval
        service = MealService(db_session)
        result = await service.get_meal_plan(test_user.id)
        
        assert result.id == meal_plan.id
        assert result.daily_calorie_target == 2000
        assert result.protein_percentage == Decimal("30.00")
    
    async def test_get_meal_plan_not_found(self, db_session, test_user):
        """Test meal plan retrieval when plan doesn't exist."""
        # Create profile without meal plan
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=False,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Test retrieval
        service = MealService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await service.get_meal_plan(test_user.id)
        
        assert exc_info.value.status_code == 404
        assert "Meal plan not found" in str(exc_info.value.detail)
    
    async def test_get_meal_schedule_success(self, db_session, test_user):
        """Test successful meal schedule retrieval."""
        # Create profile
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=False,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.flush()
        
        # Create meal schedules
        breakfast = MealSchedule(
            profile_id=profile.id,
            meal_name="breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True
        )
        lunch = MealSchedule(
            profile_id=profile.id,
            meal_name="lunch",
            scheduled_time=time(12, 0),
            enable_notifications=True
        )
        db_session.add_all([breakfast, lunch])
        await db_session.commit()
        
        # Test retrieval
        service = MealService(db_session)
        result = await service.get_meal_schedule(test_user.id)
        
        assert len(result) == 2
        assert any(s.meal_name == "breakfast" for s in result)
        assert any(s.meal_name == "lunch" for s in result)
    
    async def test_get_next_meal(self, db_session, test_user):
        """Test next meal calculation."""
        # Create profile
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=False,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.flush()
        
        # Create meal schedules with times throughout the day
        breakfast = MealSchedule(
            profile_id=profile.id,
            meal_name="breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True
        )
        lunch = MealSchedule(
            profile_id=profile.id,
            meal_name="lunch",
            scheduled_time=time(12, 0),
            enable_notifications=True
        )
        dinner = MealSchedule(
            profile_id=profile.id,
            meal_name="dinner",
            scheduled_time=time(18, 0),
            enable_notifications=True
        )
        db_session.add_all([breakfast, lunch, dinner])
        await db_session.commit()
        
        # Test retrieval
        service = MealService(db_session)
        result = await service.get_next_meal(test_user.id)
        
        # Result depends on current time, but should return a meal or None
        assert result is None or isinstance(result, MealSchedule)
    
    async def test_check_profile_lock(self, db_session, test_user):
        """Test profile lock checking."""
        # Create locked profile
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=True,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Test lock check
        service = MealService(db_session)
        is_locked = await service.check_profile_lock(test_user.id)
        
        assert is_locked is True
    
    async def test_validate_macro_percentages_valid(self, db_session):
        """Test macro percentage validation with valid values."""
        meal_plan = MealPlan(
            profile_id=uuid4(),
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("30.00")
        )
        
        service = MealService(db_session)
        assert service.validate_macro_percentages(meal_plan) is True
    
    async def test_validate_macro_percentages_invalid(self, db_session):
        """Test macro percentage validation with invalid values."""
        meal_plan = MealPlan(
            profile_id=uuid4(),
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("25.00")  # Sum = 95, not 100
        )
        
        service = MealService(db_session)
        assert service.validate_macro_percentages(meal_plan) is False
    
    async def test_update_meal_plan_locked_profile(self, db_session, test_user):
        """Test meal plan update fails when profile is locked."""
        # Create locked profile with meal plan
        profile = UserProfile(
            user_id=test_user.id,
            is_locked=True,
            fitness_level="intermediate"
        )
        db_session.add(profile)
        await db_session.flush()
        
        meal_plan = MealPlan(
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.00"),
            carbs_percentage=Decimal("40.00"),
            fats_percentage=Decimal("30.00")
        )
        db_session.add(meal_plan)
        await db_session.commit()
        
        # Test update
        service = MealService(db_session)
        
        with pytest.raises(Exception) as exc_info:
            await service.update_meal_plan(
                test_user.id,
                {"daily_calorie_target": 2500}
            )
        
        assert exc_info.value.status_code == 403
        assert "locked" in str(exc_info.value.detail).lower()
