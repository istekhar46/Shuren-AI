"""
Tests for workout endpoints.

Validates workout plan retrieval, workout day access, today's workout,
weekly workouts, and workout plan/schedule updates.
"""

import pytest
from datetime import datetime, time
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.endpoints.workouts import router
from app.models.user import User
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, ExerciseLibrary
from app.models.preferences import WorkoutSchedule


@pytest.fixture
def mock_db():
    """Create a mock database session."""
    db = AsyncMock()
    db.add = MagicMock()
    db.commit = AsyncMock()
    db.flush = AsyncMock()
    db.refresh = AsyncMock()
    db.execute = AsyncMock()
    db.delete = AsyncMock()
    return db


@pytest.fixture
def mock_user():
    """Create a mock authenticated user."""
    return User(
        id=uuid4(),
        email="test@example.com",
        full_name="Test User",
        is_active=True
    )


@pytest.fixture
def mock_exercise():
    """Create a mock exercise from library."""
    return ExerciseLibrary(
        id=uuid4(),
        exercise_name="Barbell Squat",
        exercise_slug="barbell-squat",
        exercise_type="strength",
        primary_muscle_group="quadriceps",
        secondary_muscle_groups=["glutes", "hamstrings"],
        equipment_required=["barbell", "squat_rack"],
        difficulty_level="intermediate",
        description="Compound lower body exercise",
        instructions="Stand with feet shoulder-width apart...",
        gif_url="https://example.com/squat.gif",
        is_compound=True,
        is_unilateral=False
    )


@pytest.fixture
def mock_workout_plan(mock_user, mock_exercise):
    """Create a mock workout plan with days and exercises."""
    plan = WorkoutPlan(
        id=uuid4(),
        user_id=mock_user.id,
        plan_name="Test Workout Plan",
        plan_description="A test plan",
        duration_weeks=12,
        days_per_week=4,
        plan_rationale="For testing",
        is_locked=False,
        created_at=datetime.now(),
        updated_at=datetime.now()
    )
    
    # Create workout day
    day = WorkoutDay(
        id=uuid4(),
        workout_plan_id=plan.id,
        day_number=1,
        day_name="Leg Day",
        muscle_groups=["quadriceps", "glutes"],
        workout_type="strength",
        description="Lower body workout",
        estimated_duration_minutes=60
    )
    
    # Create workout exercise
    exercise = WorkoutExercise(
        id=uuid4(),
        workout_day_id=day.id,
        exercise_library_id=mock_exercise.id,
        exercise_order=1,
        sets=4,
        reps_target=10,
        weight_kg=Decimal("100.0"),
        rest_seconds=90,
        exercise_library=mock_exercise
    )
    
    day.exercises = [exercise]
    plan.workout_days = [day]
    
    return plan


@pytest.fixture
def app(mock_db, mock_user):
    """Create FastAPI test application with mocked dependencies."""
    app = FastAPI()
    app.include_router(router, prefix="/api/v1/workouts", tags=["workouts"])
    
    # Override dependencies
    from app.db.session import get_db
    from app.core.deps import get_current_user
    
    async def override_get_db():
        yield mock_db
    
    async def override_get_current_user():
        return mock_user
    
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    
    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


class TestGetWorkoutPlan:
    """Tests for GET /api/v1/workouts/plan endpoint."""
    
    def test_get_workout_plan_success(self, client, mock_db, mock_workout_plan):
        """Test successful workout plan retrieval."""
        # Mock WorkoutService.get_workout_plan
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_workout_plan = AsyncMock(return_value=mock_workout_plan)
            
            response = client.get("/api/v1/workouts/plan")
            
            assert response.status_code == 200
            data = response.json()
            assert data["plan_name"] == "Test Workout Plan"
            assert data["duration_weeks"] == 12
            assert len(data["workout_days"]) == 1
            assert data["workout_days"][0]["day_name"] == "Leg Day"
    
    def test_get_workout_plan_not_found(self, client, mock_db):
        """Test workout plan not found returns 404."""
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_workout_plan = AsyncMock(
                side_effect=HTTPException(status_code=404, detail="Workout plan not found")
            )
            
            response = client.get("/api/v1/workouts/plan")
            
            assert response.status_code == 404


class TestGetWorkoutDay:
    """Tests for GET /api/v1/workouts/plan/day/{day_number} endpoint."""
    
    def test_get_workout_day_success(self, client, mock_db, mock_workout_plan):
        """Test successful workout day retrieval."""
        workout_day = mock_workout_plan.workout_days[0]
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_workout_day = AsyncMock(return_value=workout_day)
            
            response = client.get("/api/v1/workouts/plan/day/1")
            
            assert response.status_code == 200
            data = response.json()
            assert data["day_number"] == 1
            assert data["day_name"] == "Leg Day"
            assert len(data["exercises"]) == 1
    
    def test_get_workout_day_invalid_number(self, client, mock_db):
        """Test invalid day number returns 422."""
        response = client.get("/api/v1/workouts/plan/day/8")
        
        assert response.status_code == 422


class TestGetTodayWorkout:
    """Tests for GET /api/v1/workouts/today endpoint."""
    
    def test_get_today_workout_success(self, client, mock_db, mock_workout_plan):
        """Test successful today's workout retrieval."""
        workout_day = mock_workout_plan.workout_days[0]
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_today_workout = AsyncMock(return_value=workout_day)
            
            response = client.get("/api/v1/workouts/today")
            
            assert response.status_code == 200
            data = response.json()
            assert data["day_name"] == "Leg Day"
    
    def test_get_today_workout_none_scheduled(self, client, mock_db):
        """Test no workout scheduled today returns 404."""
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_today_workout = AsyncMock(return_value=None)
            
            response = client.get("/api/v1/workouts/today")
            
            assert response.status_code == 404
            assert "No workout scheduled" in response.json()["detail"]


class TestGetWeekWorkouts:
    """Tests for GET /api/v1/workouts/week endpoint."""
    
    def test_get_week_workouts_success(self, client, mock_db, mock_workout_plan):
        """Test successful weekly workouts retrieval."""
        workout_days = mock_workout_plan.workout_days
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_week_workouts = AsyncMock(return_value=workout_days)
            
            response = client.get("/api/v1/workouts/week")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
            assert len(data) == 1


class TestUpdateWorkoutPlan:
    """Tests for PATCH /api/v1/workouts/plan endpoint."""
    
    def test_update_workout_plan_success(self, client, mock_db, mock_workout_plan):
        """Test successful workout plan update."""
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.update_workout_plan = AsyncMock(return_value=mock_workout_plan)
            
            response = client.patch(
                "/api/v1/workouts/plan",
                json={"plan_name": "Updated Plan"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert "plan_name" in data
    
    def test_update_workout_plan_locked_profile(self, client, mock_db):
        """Test updating locked profile returns 403."""
        from fastapi import HTTPException
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.update_workout_plan = AsyncMock(
                side_effect=HTTPException(status_code=403, detail="Profile is locked")
            )
            
            response = client.patch(
                "/api/v1/workouts/plan",
                json={"plan_name": "Updated Plan"}
            )
            
            assert response.status_code == 403


class TestGetWorkoutSchedule:
    """Tests for GET /api/v1/workouts/schedule endpoint."""
    
    def test_get_workout_schedule_success(self, client, mock_db, mock_user):
        """Test successful workout schedule retrieval."""
        mock_schedule = WorkoutSchedule(
            id=uuid4(),
            profile_id=uuid4(),
            day_of_week=0,
            scheduled_time=time(9, 0),
            enable_notifications=True
        )
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.get_workout_schedule = AsyncMock(return_value=[mock_schedule])
            
            response = client.get("/api/v1/workouts/schedule")
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)


class TestUpdateWorkoutSchedule:
    """Tests for PATCH /api/v1/workouts/schedule endpoint."""
    
    def test_update_workout_schedule_success(self, client, mock_db, mock_user):
        """Test successful workout schedule update."""
        mock_schedule = WorkoutSchedule(
            id=uuid4(),
            profile_id=uuid4(),
            day_of_week=0,
            scheduled_time=time(10, 0),
            enable_notifications=True
        )
        
        with patch('app.api.v1.endpoints.workouts.WorkoutService') as MockService:
            mock_service = MockService.return_value
            mock_service.update_workout_schedule = AsyncMock(return_value=[mock_schedule])
            
            response = client.patch(
                "/api/v1/workouts/schedule",
                json={"preferred_workout_time": "10:00:00"}
            )
            
            assert response.status_code == 200
            data = response.json()
            assert isinstance(data, list)
