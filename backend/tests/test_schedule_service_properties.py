"""
Property-based tests for schedule service correctness.

These tests use Hypothesis to verify that schedule query operations
maintain correctness properties across all possible inputs.

**Property 3: Schedule Query Returns Complete Data**

**Validates: Requirements US-3.1, US-3.2 from general-agent-delegation-tools spec**
"""

import pytest
from datetime import datetime, timezone, time
from uuid import uuid4

from hypothesis import given, strategies as st, settings, HealthCheck
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import WorkoutSchedule, MealSchedule
from app.services.schedule_service import ScheduleService


# Hypothesis strategies for generating test data
@st.composite
def workout_schedule_data(draw):
    """Generate random workout schedule data."""
    return {
        "day_of_week": draw(st.integers(min_value=0, max_value=6)),
        "scheduled_time": time(
            hour=draw(st.integers(min_value=0, max_value=23)),
            minute=draw(st.integers(min_value=0, max_value=59))
        ),
        "enable_notifications": draw(st.booleans())
    }


@st.composite
def meal_schedule_data(draw):
    """Generate random meal schedule data."""
    return {
        "meal_name": draw(st.sampled_from([
            "breakfast", "lunch", "dinner", "snack_1", "snack_2",
            "pre_workout", "post_workout"
        ])),
        "scheduled_time": time(
            hour=draw(st.integers(min_value=0, max_value=23)),
            minute=draw(st.integers(min_value=0, max_value=59))
        ),
        "enable_notifications": draw(st.booleans())
    }


class TestScheduleQueryCompleteness:
    """
    Property 3: Schedule Query Returns Complete Data
    
    For any user with schedules configured, querying upcoming schedules should
    return both workout and meal schedules with all required fields: id, 
    day/time information, and notification settings.
    
    **Validates: Requirements US-3.1, US-3.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_workout_schedules=st.integers(min_value=1, max_value=7),
        num_meal_schedules=st.integers(min_value=1, max_value=7),
        data=st.data()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_schedule_query_returns_complete_data(
        self,
        db_session: AsyncSession,
        num_workout_schedules: int,
        num_meal_schedules: int,
        data
    ):
        """
        Property: Schedule query returns all required fields.
        
        Given a user with workout and meal schedules configured,
        when querying upcoming schedules,
        then the response should contain all required fields with valid data.
        
        Feature: general-agent-delegation-tools, Property 3: Schedule Query Returns Complete Data
        """
        # Arrange: Create user with profile
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.flush()
        
        # Create workout schedules
        workout_schedule_ids = []
        for i in range(num_workout_schedules):
            schedule_data = data.draw(workout_schedule_data())
            
            workout_schedule = WorkoutSchedule(
                id=uuid4(),
                profile_id=profile.id,
                day_of_week=schedule_data["day_of_week"],
                scheduled_time=schedule_data["scheduled_time"],
                enable_notifications=schedule_data["enable_notifications"],
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(workout_schedule)
            workout_schedule_ids.append(workout_schedule.id)
        
        # Create meal schedules
        meal_schedule_ids = []
        for i in range(num_meal_schedules):
            schedule_data = data.draw(meal_schedule_data())
            
            meal_schedule = MealSchedule(
                id=uuid4(),
                profile_id=profile.id,
                meal_name=schedule_data["meal_name"],
                scheduled_time=schedule_data["scheduled_time"],
                enable_notifications=schedule_data["enable_notifications"],
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(meal_schedule)
            meal_schedule_ids.append(meal_schedule.id)
        
        await db_session.commit()
        
        # Act: Query upcoming schedules
        result = await ScheduleService.get_upcoming_schedule(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Verify all required fields are present and valid
        assert result is not None, "Schedule query should return data when schedules are configured"
        
        # Verify top-level required fields
        assert "workouts" in result, "Response must contain 'workouts'"
        assert "meals" in result, "Response must contain 'meals'"
        
        # Verify workouts list
        assert isinstance(result["workouts"], list), "Workouts must be a list"
        assert len(result["workouts"]) == num_workout_schedules, \
            f"Should have {num_workout_schedules} workout schedules"
        
        # Verify each workout schedule has required fields
        day_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        
        for workout in result["workouts"]:
            assert "id" in workout, "Workout schedule must have 'id'"
            assert "day" in workout, "Workout schedule must have 'day'"
            assert "day_of_week" in workout, "Workout schedule must have 'day_of_week'"
            assert "time" in workout, "Workout schedule must have 'time'"
            assert "notifications_enabled" in workout, "Workout schedule must have 'notifications_enabled'"
            
            # Verify field types
            assert isinstance(workout["id"], str), "Workout schedule id must be string (UUID)"
            assert isinstance(workout["day"], str), "Day must be string"
            assert isinstance(workout["day_of_week"], int), "Day of week must be integer"
            assert isinstance(workout["time"], str), "Time must be string (ISO format)"
            assert isinstance(workout["notifications_enabled"], bool), "Notifications enabled must be bool"
            
            # Verify value ranges and consistency
            assert workout["day_of_week"] >= 0 and workout["day_of_week"] <= 6, \
                "Day of week must be 0-6"
            assert workout["day"] in day_names, "Day must be a valid day name"
            assert workout["day"] == day_names[workout["day_of_week"]], \
                "Day name must match day_of_week integer"
            
            # Verify UUID format
            assert len(workout["id"]) == 36, "ID should be UUID string format"
            
            # Verify time format (ISO format HH:MM:SS)
            assert ":" in workout["time"], "Time should be in ISO format"
        
        # Verify meals list
        assert isinstance(result["meals"], list), "Meals must be a list"
        assert len(result["meals"]) == num_meal_schedules, \
            f"Should have {num_meal_schedules} meal schedules"
        
        # Verify each meal schedule has required fields
        for meal in result["meals"]:
            assert "id" in meal, "Meal schedule must have 'id'"
            assert "meal_name" in meal, "Meal schedule must have 'meal_name'"
            assert "time" in meal, "Meal schedule must have 'time'"
            assert "notifications_enabled" in meal, "Meal schedule must have 'notifications_enabled'"
            
            # Verify field types
            assert isinstance(meal["id"], str), "Meal schedule id must be string (UUID)"
            assert isinstance(meal["meal_name"], str), "Meal name must be string"
            assert isinstance(meal["time"], str), "Time must be string (ISO format)"
            assert isinstance(meal["notifications_enabled"], bool), "Notifications enabled must be bool"
            
            # Verify UUID format
            assert len(meal["id"]) == 36, "ID should be UUID string format"
            
            # Verify time format (ISO format HH:MM:SS)
            assert ":" in meal["time"], "Time should be in ISO format"
            
            # Verify meal name is not empty
            assert len(meal["meal_name"]) > 0, "Meal name should not be empty"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_schedule_query_returns_empty_lists_when_no_schedules(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Schedule query returns empty lists when no schedules configured.
        
        Given a user without any schedules,
        when querying upcoming schedules,
        then the response should contain empty workout and meal lists.
        
        Feature: general-agent-delegation-tools, Property 3: Schedule Query Returns Complete Data
        """
        # Arrange: Create user with profile but no schedules
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        # Act: Query upcoming schedules
        result = await ScheduleService.get_upcoming_schedule(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Should return empty lists when no schedules configured
        assert result is not None, "Should return dict even when no schedules"
        assert "workouts" in result, "Response must contain 'workouts'"
        assert "meals" in result, "Response must contain 'meals'"
        assert result["workouts"] == [], "Workouts should be empty list"
        assert result["meals"] == [], "Meals should be empty list"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_schedule_query_raises_error_for_nonexistent_user(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Schedule query raises ValueError for nonexistent user.
        
        Given a nonexistent user ID,
        when querying upcoming schedules,
        then a ValueError should be raised.
        
        Feature: general-agent-delegation-tools, Property 3: Schedule Query Returns Complete Data
        """
        # Arrange: Use a random UUID that doesn't exist
        nonexistent_user_id = uuid4()
        
        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="User profile not found"):
            await ScheduleService.get_upcoming_schedule(
                user_id=nonexistent_user_id,
                db_session=db_session
            )
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        num_workout_schedules=st.integers(min_value=0, max_value=5),
        num_meal_schedules=st.integers(min_value=0, max_value=5),
        data=st.data()
    )
    @settings(
        max_examples=30,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_schedule_query_filters_soft_deleted_schedules(
        self,
        db_session: AsyncSession,
        num_workout_schedules: int,
        num_meal_schedules: int,
        data
    ):
        """
        Property: Schedule query filters out soft-deleted schedules.
        
        Given a user with some schedules soft-deleted,
        when querying upcoming schedules,
        then only active schedules should be returned.
        
        Feature: general-agent-delegation-tools, Property 3: Schedule Query Returns Complete Data
        """
        # Arrange: Create user with profile
        user = User(
            id=uuid4(),
            email=f"test_{uuid4()}@example.com",
            hashed_password="hashed",
            full_name="Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.flush()
        
        # Create workout schedules (some will be soft-deleted)
        active_workout_count = 0
        for i in range(num_workout_schedules):
            schedule_data = data.draw(workout_schedule_data())
            should_delete = data.draw(st.booleans())
            
            workout_schedule = WorkoutSchedule(
                id=uuid4(),
                profile_id=profile.id,
                day_of_week=schedule_data["day_of_week"],
                scheduled_time=schedule_data["scheduled_time"],
                enable_notifications=schedule_data["enable_notifications"],
                created_at=datetime.now(timezone.utc),
                deleted_at=datetime.now(timezone.utc) if should_delete else None
            )
            db_session.add(workout_schedule)
            
            if not should_delete:
                active_workout_count += 1
        
        # Create meal schedules (some will be soft-deleted)
        active_meal_count = 0
        for i in range(num_meal_schedules):
            schedule_data = data.draw(meal_schedule_data())
            should_delete = data.draw(st.booleans())
            
            meal_schedule = MealSchedule(
                id=uuid4(),
                profile_id=profile.id,
                meal_name=schedule_data["meal_name"],
                scheduled_time=schedule_data["scheduled_time"],
                enable_notifications=schedule_data["enable_notifications"],
                created_at=datetime.now(timezone.utc),
                deleted_at=datetime.now(timezone.utc) if should_delete else None
            )
            db_session.add(meal_schedule)
            
            if not should_delete:
                active_meal_count += 1
        
        await db_session.commit()
        
        # Act: Query upcoming schedules
        result = await ScheduleService.get_upcoming_schedule(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Only active schedules should be returned
        assert result is not None, "Schedule query should return data"
        assert len(result["workouts"]) == active_workout_count, \
            f"Should only return {active_workout_count} active workout schedules"
        assert len(result["meals"]) == active_meal_count, \
            f"Should only return {active_meal_count} active meal schedules"
