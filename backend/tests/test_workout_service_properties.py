"""
Property-based tests for workout service correctness.

These tests use Hypothesis to verify that workout query operations
maintain correctness properties across all possible inputs.

**Property 1: Workout Query Returns Complete Data**

**Validates: Requirements US-1.1, US-1.2 from general-agent-delegation-tools spec**
"""

import pytest
from datetime import datetime, timezone, time
from uuid import uuid4
from decimal import Decimal

from hypothesis import given, strategies as st, settings, HealthCheck, assume
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.profile import UserProfile
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, ExerciseLibrary
from app.models.preferences import WorkoutSchedule
from app.services.workout_service import WorkoutService


# Hypothesis strategies for generating test data
@st.composite
def workout_day_data(draw):
    """Generate random workout day data."""
    day_number = draw(st.integers(min_value=1, max_value=7))
    
    return {
        "day_number": day_number,
        "day_name": draw(st.sampled_from([
            "Push Day", "Pull Day", "Leg Day", "Upper Body", 
            "Lower Body", "Full Body", "Cardio Day"
        ])),
        "muscle_groups": draw(st.lists(
            st.sampled_from([
                "chest", "back", "shoulders", "biceps", "triceps",
                "legs", "core", "glutes", "hamstrings", "quads"
            ]),
            min_size=1,
            max_size=4,
            unique=True
        )),
        "workout_type": draw(st.sampled_from([
            "strength", "cardio", "hiit", "active_recovery"
        ])),
        "estimated_duration_minutes": draw(st.integers(min_value=30, max_value=120))
    }


@st.composite
def exercise_data(draw):
    """Generate random exercise data."""
    # Decide if we use target reps or min/max range
    use_target = draw(st.booleans())
    
    if use_target:
        reps_target = draw(st.integers(min_value=1, max_value=30))
        reps_min = None
        reps_max = None
    else:
        reps_min = draw(st.integers(min_value=1, max_value=20))
        reps_max = draw(st.integers(min_value=reps_min, max_value=30))
        reps_target = None
    
    return {
        "sets": draw(st.integers(min_value=1, max_value=10)),
        "reps_target": reps_target,
        "reps_min": reps_min,
        "reps_max": reps_max,
        "weight_kg": draw(st.one_of(
            st.none(),
            st.decimals(min_value=Decimal("2.5"), max_value=Decimal("200"), places=2)
        )),
        "rest_seconds": draw(st.integers(min_value=30, max_value=300)),
        "notes": draw(st.one_of(
            st.none(),
            st.text(
                min_size=0, 
                max_size=200, 
                alphabet=st.characters(
                    min_codepoint=32,  # Start from space character
                    max_codepoint=126,  # End at tilde (printable ASCII)
                    blacklist_characters="\x00"
                )
            )
        ))
    }


class TestWorkoutQueryCompleteness:
    """
    Property 1: Workout Query Returns Complete Data
    
    For any user with a workout plan, querying today's workout should return
    all required fields: day_name, workout_type, muscle_groups, 
    estimated_duration_minutes, and a list of exercises with sets, reps, rest_seconds.
    
    **Validates: Requirements US-1.1, US-1.2**
    """
    
    @pytest.mark.asyncio
    @pytest.mark.property
    @given(
        workout_data=workout_day_data(),
        num_exercises=st.integers(min_value=1, max_value=8),
        day_of_week=st.integers(min_value=0, max_value=6),
        data=st.data()
    )
    @settings(
        max_examples=20,
        deadline=None,
        suppress_health_check=[HealthCheck.function_scoped_fixture, HealthCheck.too_slow]
    )
    async def test_workout_query_returns_complete_data(
        self,
        db_session: AsyncSession,
        workout_data: dict,
        num_exercises: int,
        day_of_week: int,
        data
    ):
        """
        Property: Workout query returns all required fields.
        
        Given a user with a workout plan scheduled for today,
        when querying today's workout,
        then the response should contain all required fields with valid data.
        
        Feature: general-agent-delegation-tools, Property 1: Workout Query Returns Complete Data
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
        
        # Create workout schedule for today
        # Map day_of_week to day_number (1-7)
        day_number = day_of_week + 1
        
        workout_schedule = WorkoutSchedule(
            id=uuid4(),
            profile_id=profile.id,
            day_of_week=day_of_week,
            scheduled_time=time(18, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_schedule)
        
        # Create workout plan
        workout_plan = WorkoutPlan(
            id=uuid4(),
            user_id=user.id,
            plan_name="Test Plan",
            duration_weeks=4,
            days_per_week=3,
            is_locked=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_plan)
        
        # Create workout day matching today
        workout_day = WorkoutDay(
            id=uuid4(),
            workout_plan_id=workout_plan.id,
            day_number=day_number,
            day_name=workout_data["day_name"],
            muscle_groups=workout_data["muscle_groups"],
            workout_type=workout_data["workout_type"],
            estimated_duration_minutes=workout_data["estimated_duration_minutes"],
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_day)
        
        # Create exercise library entries and workout exercises
        for i in range(num_exercises):
            # Use UUID to ensure unique exercise names across test runs
            unique_id = uuid4().hex[:8]
            exercise_lib = ExerciseLibrary(
                id=uuid4(),
                exercise_name=f"Exercise {i+1} {unique_id}",
                exercise_slug=f"exercise-{i+1}-{uuid4()}",
                exercise_type="strength",
                primary_muscle_group=workout_data["muscle_groups"][0],
                equipment_required=["dumbbells"],
                difficulty_level="intermediate",
                description="Test exercise",
                instructions="Test instructions",
                is_compound=False,
                is_unilateral=False,
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(exercise_lib)
            
            # Generate exercise data using data strategy
            ex_data = data.draw(exercise_data())
            
            workout_exercise = WorkoutExercise(
                id=uuid4(),
                workout_day_id=workout_day.id,
                exercise_library_id=exercise_lib.id,
                exercise_order=i + 1,
                sets=ex_data["sets"],
                reps_target=ex_data["reps_target"],
                reps_min=ex_data["reps_min"],
                reps_max=ex_data["reps_max"],
                weight_kg=ex_data["weight_kg"],
                rest_seconds=ex_data["rest_seconds"],
                notes=ex_data["notes"],
                created_at=datetime.now(timezone.utc)
            )
            db_session.add(workout_exercise)
        
        await db_session.commit()
        
        # Mock datetime.now() to return the test day_of_week
        # We'll use a different approach - just test with current day
        # Since we can't easily mock datetime in the service, we'll create
        # a workout for the actual current day
        current_day = datetime.now().weekday()
        
        # Update workout schedule and day to match current day
        workout_schedule.day_of_week = current_day
        workout_day.day_number = current_day + 1
        await db_session.commit()
        
        # Act: Query today's workout
        result = await WorkoutService.get_today_workout(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Verify all required fields are present and valid
        assert result is not None, "Workout query should return data when workout is scheduled"
        
        # Verify top-level required fields
        assert "day_name" in result, "Response must contain 'day_name'"
        assert "workout_type" in result, "Response must contain 'workout_type'"
        assert "muscle_groups" in result, "Response must contain 'muscle_groups'"
        assert "estimated_duration_minutes" in result, "Response must contain 'estimated_duration_minutes'"
        assert "exercises" in result, "Response must contain 'exercises'"
        
        # Verify field values match input
        assert result["day_name"] == workout_data["day_name"]
        assert result["workout_type"] == workout_data["workout_type"]
        assert result["muscle_groups"] == workout_data["muscle_groups"]
        assert result["estimated_duration_minutes"] == workout_data["estimated_duration_minutes"]
        
        # Verify exercises list
        assert isinstance(result["exercises"], list), "Exercises must be a list"
        assert len(result["exercises"]) == num_exercises, f"Should have {num_exercises} exercises"
        
        # Verify each exercise has required fields
        for exercise in result["exercises"]:
            assert "name" in exercise, "Exercise must have 'name'"
            assert "sets" in exercise, "Exercise must have 'sets'"
            assert "reps" in exercise, "Exercise must have 'reps'"
            assert "weight_kg" in exercise, "Exercise must have 'weight_kg' (can be None)"
            assert "rest_seconds" in exercise, "Exercise must have 'rest_seconds'"
            assert "notes" in exercise, "Exercise must have 'notes' (can be None)"
            
            # Verify field types
            assert isinstance(exercise["name"], str), "Exercise name must be string"
            assert isinstance(exercise["sets"], int), "Sets must be integer"
            assert isinstance(exercise["reps"], str), "Reps must be string"
            assert exercise["weight_kg"] is None or isinstance(exercise["weight_kg"], float), \
                "Weight must be float or None"
            assert isinstance(exercise["rest_seconds"], int), "Rest seconds must be integer"
            assert exercise["notes"] is None or isinstance(exercise["notes"], str), \
                "Notes must be string or None"
            
            # Verify value ranges
            assert exercise["sets"] >= 1, "Sets must be at least 1"
            assert exercise["rest_seconds"] >= 0, "Rest seconds must be non-negative"
            if exercise["weight_kg"] is not None:
                assert exercise["weight_kg"] > 0, "Weight must be positive if specified"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_workout_query_returns_none_when_no_schedule(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Workout query returns None when no workout is scheduled.
        
        Given a user with a workout plan but no schedule for today,
        when querying today's workout,
        then the response should be None.
        
        Feature: general-agent-delegation-tools, Property 1: Workout Query Returns Complete Data
        """
        # Arrange: Create user with profile but no workout schedule for today
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
        
        # Create workout plan but no schedule for today
        workout_plan = WorkoutPlan(
            id=uuid4(),
            user_id=user.id,
            plan_name="Test Plan",
            duration_weeks=4,
            days_per_week=3,
            is_locked=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_plan)
        
        await db_session.commit()
        
        # Act: Query today's workout
        result = await WorkoutService.get_today_workout(
            user_id=user.id,
            db_session=db_session
        )
        
        # Assert: Should return None when no workout scheduled
        assert result is None, "Should return None when no workout is scheduled for today"
    
    @pytest.mark.asyncio
    @pytest.mark.property
    async def test_workout_query_raises_error_for_nonexistent_user(
        self,
        db_session: AsyncSession
    ):
        """
        Property: Workout query raises ValueError for nonexistent user.
        
        Given a nonexistent user ID,
        when querying today's workout,
        then a ValueError should be raised.
        
        Feature: general-agent-delegation-tools, Property 1: Workout Query Returns Complete Data
        """
        # Arrange: Use a random UUID that doesn't exist
        nonexistent_user_id = uuid4()
        
        # Act & Assert: Should raise ValueError
        with pytest.raises(ValueError, match="User profile not found"):
            await WorkoutService.get_today_workout(
                user_id=nonexistent_user_id,
                db_session=db_session
            )
