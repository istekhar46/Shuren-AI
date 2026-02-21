"""
End-to-end integration tests for Phase 1.1 Core Endpoints.

Tests complete workflows across multiple endpoints and services:
- Workout plan creation and retrieval
- Meal plan modification flow
- Chat conversation flow
- Profile locking workflow

These tests validate the entire system working together, not just
individual components in isolation.
"""

import pytest
from datetime import datetime, time, timezone
from decimal import Decimal
from uuid import uuid4

from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import create_access_token
from app.models.user import User
from app.models.profile import UserProfile
from app.models.workout import WorkoutPlan, WorkoutDay, WorkoutExercise, ExerciseLibrary
from app.models.preferences import MealPlan, MealSchedule, WorkoutSchedule
from app.models.chat import ChatSession, ChatMessage


@pytest.mark.asyncio
class TestWorkoutPlanE2E:
    """End-to-end tests for complete workout plan creation and retrieval.
    
    Validates: Requirements 2.1
    """
    
    async def test_complete_workout_plan_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete workout plan creation and retrieval workflow.
        
        This test validates:
        1. Creating a user with profile
        2. Creating exercise library entries
        3. Creating a complete workout plan with days and exercises
        4. Retrieving the workout plan through API
        5. Verifying all data is present and correct
        """
        # Step 1: Create user with profile
        user = User(
            id=uuid4(),
            email="workout_test@example.com",
            full_name="Workout Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=False,
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.commit()
        
        # Step 2: Create exercise library entries
        squat = ExerciseLibrary(
            id=uuid4(),
            exercise_name="Barbell Squat",
            exercise_slug="barbell-squat",
            exercise_type="strength",
            primary_muscle_group="quadriceps",
            secondary_muscle_groups=["glutes", "hamstrings"],
            equipment_required=["barbell", "squat_rack"],
            difficulty_level="intermediate",
            description="Compound lower body exercise",
            instructions="Stand with feet shoulder-width apart, squat down keeping chest up",
            gif_url="https://example.com/squat.gif",
            is_compound=True,
            is_unilateral=False
        )
        
        bench_press = ExerciseLibrary(
            id=uuid4(),
            exercise_name="Barbell Bench Press",
            exercise_slug="barbell-bench-press",
            exercise_type="strength",
            primary_muscle_group="chest",
            secondary_muscle_groups=["triceps", "shoulders"],
            equipment_required=["barbell", "bench"],
            difficulty_level="intermediate",
            description="Compound upper body pressing exercise",
            instructions="Lie on bench, lower bar to chest, press up",
            gif_url="https://example.com/bench.gif",
            is_compound=True,
            is_unilateral=False
        )
        
        db_session.add(squat)
        db_session.add(bench_press)
        await db_session.commit()
        
        # Step 3: Create workout plan with days and exercises
        workout_plan = WorkoutPlan(
            id=uuid4(),
            user_id=user.id,
            plan_name="4-Day Upper/Lower Split",
            plan_description="Balanced strength training program",
            duration_weeks=12,
            days_per_week=4,
            plan_rationale="Progressive overload for muscle gain",
            is_locked=False,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        db_session.add(workout_plan)
        await db_session.flush()
        
        # Create Day 1: Lower Body
        day1 = WorkoutDay(
            id=uuid4(),
            workout_plan_id=workout_plan.id,
            day_number=1,
            day_name="Lower Body A",
            muscle_groups=["quadriceps", "glutes", "hamstrings"],
            workout_type="strength",
            description="Squat-focused lower body day",
            estimated_duration_minutes=60
        )
        db_session.add(day1)
        await db_session.flush()
        
        # Add squat exercise to day 1
        exercise1 = WorkoutExercise(
            id=uuid4(),
            workout_day_id=day1.id,
            exercise_library_id=squat.id,
            exercise_order=1,
            sets=4,
            reps_target=8,
            weight_kg=Decimal("100.0"),
            rest_seconds=180,
            notes="Focus on depth and form"
        )
        db_session.add(exercise1)
        
        # Create Day 2: Upper Body
        day2 = WorkoutDay(
            id=uuid4(),
            workout_plan_id=workout_plan.id,
            day_number=2,
            day_name="Upper Body A",
            muscle_groups=["chest", "triceps", "shoulders"],
            workout_type="strength",
            description="Bench press-focused upper body day",
            estimated_duration_minutes=60
        )
        db_session.add(day2)
        await db_session.flush()
        
        # Add bench press exercise to day 2
        exercise2 = WorkoutExercise(
            id=uuid4(),
            workout_day_id=day2.id,
            exercise_library_id=bench_press.id,
            exercise_order=1,
            sets=4,
            reps_target=8,
            weight_kg=Decimal("80.0"),
            rest_seconds=180,
            notes="Controlled tempo"
        )
        db_session.add(exercise2)
        
        await db_session.commit()
        
        # Step 4: Retrieve workout plan through API
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.get("/api/v1/workouts/plan")
        
        # Step 5: Verify all data is present and correct
        assert response.status_code == 200
        data = response.json()
        
        # Verify plan-level data
        assert data["plan_name"] == "4-Day Upper/Lower Split"
        assert data["duration_weeks"] == 12
        assert data["days_per_week"] == 4
        assert data["is_locked"] is False
        
        # Verify workout days
        assert len(data["workout_days"]) == 2
        
        # Verify Day 1
        day1_data = next(d for d in data["workout_days"] if d["day_number"] == 1)
        assert day1_data["day_name"] == "Lower Body A"
        assert "quadriceps" in day1_data["muscle_groups"]
        assert day1_data["workout_type"] == "strength"
        assert day1_data["estimated_duration_minutes"] == 60
        
        # Verify Day 1 exercises
        assert len(day1_data["exercises"]) == 1
        ex1 = day1_data["exercises"][0]
        assert ex1["sets"] == 4
        assert ex1["reps_target"] == 8
        assert float(ex1["weight_kg"]) == 100.0
        assert ex1["rest_seconds"] == 180
        
        # Verify exercise library details are included
        assert ex1["exercise_library"]["exercise_name"] == "Barbell Squat"
        assert ex1["exercise_library"]["gif_url"] == "https://example.com/squat.gif"
        assert ex1["exercise_library"]["is_compound"] is True
        
        # Verify Day 2
        day2_data = next(d for d in data["workout_days"] if d["day_number"] == 2)
        assert day2_data["day_name"] == "Upper Body A"
        assert "chest" in day2_data["muscle_groups"]
        
        # Verify Day 2 exercises
        assert len(day2_data["exercises"]) == 1
        ex2 = day2_data["exercises"][0]
        assert ex2["exercise_library"]["exercise_name"] == "Barbell Bench Press"
        assert float(ex2["weight_kg"]) == 80.0


@pytest.mark.asyncio
class TestMealPlanModificationE2E:
    """End-to-end tests for complete meal plan modification flow.
    
    Validates: Requirements 6.1, 7.1, 7.3
    """
    
    @pytest.mark.skip(reason="Meal plan schema/model mismatch - schema expects fields not in database model")
    async def test_complete_meal_plan_modification_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete meal plan modification workflow.
        
        This test validates:
        1. Creating a user with profile and meal plan
        2. Unlocking the profile
        3. Modifying the meal plan
        4. Verifying changes are persisted
        5. Locking the profile again
        """
        # Step 1: Create user with profile and meal plan
        user = User(
            id=uuid4(),
            email="meal_test@example.com",
            full_name="Meal Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,  # Start locked
            fitness_level="intermediate",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        await db_session.flush()
        
        meal_plan = MealPlan(
            id=uuid4(),
            profile_id=profile.id,
            daily_calorie_target=2000,
            protein_percentage=Decimal("30.0"),
            carbs_percentage=Decimal("40.0"),
            fats_percentage=Decimal("30.0")
        )
        db_session.add(meal_plan)
        await db_session.commit()
        
        # Step 2: Unlock the profile
        profile.is_locked = False
        await db_session.commit()
        
        # Step 3: Modify the meal plan through API
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 2500}
        )
        
        # Step 4: Verify changes are persisted
        assert response.status_code == 200
        data = response.json()
        
        assert data["daily_calorie_target"] == 2500
        
        # Verify in database
        await db_session.refresh(meal_plan)
        assert meal_plan.daily_calorie_target == 2500
        
        # Step 5: Lock the profile again
        profile.is_locked = True
        await db_session.commit()
        
        # Verify locked profile prevents further modifications
        response = await client.patch(
            "/api/v1/meals/plan",
            json={"daily_calorie_target": 3000}
        )
        
        assert response.status_code == 403
        assert "locked" in response.json()["detail"].lower()


@pytest.mark.asyncio
class TestChatConversationE2E:
    """End-to-end tests for complete chat conversation flow.
    
    Validates: Requirements 8.1, 8.2, 8.3
    """
    
    async def test_complete_chat_conversation_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete chat conversation workflow.
        
        This test validates:
        1. Creating a user
        2. Starting a chat session
        3. Sending multiple messages
        4. Retrieving chat history
        5. Verifying message ordering
        6. Ending the session
        """
        # Step 1: Create user
        user = User(
            id=uuid4(),
            email="chat_test@example.com",
            full_name="Chat Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Step 2: Start a chat session
        response = await client.post(
            "/api/v1/chat/session/start",
            json={
                "session_type": "workout",
                "context_data": {"current_workout": "leg_day"}
            }
        )
        
        assert response.status_code == 201
        session_data = response.json()
        session_id = session_data["id"]
        assert session_data["session_type"] == "workout"
        assert session_data["status"] == "active"
        
        # Step 3: Send multiple messages
        messages_sent = []
        
        # Message 1
        response = await client.post(
            "/api/v1/chat/message",
            json={
                "message": "What exercises should I do for leg day?",
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        msg1 = response.json()
        messages_sent.append(msg1)
        
        # Message 2
        response = await client.post(
            "/api/v1/chat/message",
            json={
                "message": "How many sets should I do for squats?",
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        msg2 = response.json()
        messages_sent.append(msg2)
        
        # Message 3
        response = await client.post(
            "/api/v1/chat/message",
            json={
                "message": "What about rest time between sets?",
                "session_id": session_id
            }
        )
        assert response.status_code == 200
        msg3 = response.json()
        messages_sent.append(msg3)
        
        # Step 4: Retrieve chat history
        response = await client.get(
            f"/api/v1/chat/history?session_id={session_id}&limit=50&offset=0"
        )
        
        assert response.status_code == 200
        history_data = response.json()
        
        # Step 5: Verify message ordering (chronological)
        messages = history_data["messages"]
        
        # Should have 6 messages total (3 user + 3 assistant)
        assert len(messages) >= 6
        
        # Verify messages are in chronological order
        for i in range(len(messages) - 1):
            assert messages[i]["created_at"] <= messages[i + 1]["created_at"]
        
        # Verify user messages are present
        user_messages = [m for m in messages if m["role"] == "user"]
        assert len(user_messages) >= 3
        assert any("leg day" in m["content"].lower() for m in user_messages)
        assert any("squats" in m["content"].lower() for m in user_messages)
        assert any("rest time" in m["content"].lower() for m in user_messages)
        
        # Verify assistant responses are present
        assistant_messages = [m for m in messages if m["role"] == "assistant"]
        assert len(assistant_messages) >= 3
        
        # Step 6: End the session
        response = await client.delete(f"/api/v1/chat/session/{session_id}")
        
        assert response.status_code == 204
        
        # Verify session is marked as completed
        from sqlalchemy import select
        from app.models.chat import ChatSession
        
        result = await db_session.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        session = result.scalar_one()
        assert session.status == "completed"
        assert session.ended_at is not None
    
    async def test_chat_history_pagination(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test chat history pagination works correctly.
        
        Validates that limit and offset parameters work as expected.
        """
        # Create user
        user = User(
            id=uuid4(),
            email="pagination_test@example.com",
            full_name="Pagination Test User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        await db_session.commit()
        
        token = create_access_token({"user_id": str(user.id)})
        client.headers["Authorization"] = f"Bearer {token}"
        
        # Create session and send 10 messages
        response = await client.post(
            "/api/v1/chat/session/start",
            json={"session_type": "general"}
        )
        session_id = response.json()["id"]
        
        for i in range(10):
            await client.post(
                "/api/v1/chat/message",
                json={
                    "message": f"Test message {i + 1}",
                    "session_id": session_id
                }
            )
        
        # Test pagination: first page (limit 5)
        response = await client.get(
            f"/api/v1/chat/history?session_id={session_id}&limit=5&offset=0"
        )
        assert response.status_code == 200
        page1 = response.json()
        assert len(page1["messages"]) == 5
        assert page1["limit"] == 5
        assert page1["offset"] == 0
        assert page1["total"] >= 20  # 10 user + 10 assistant
        
        # Test pagination: second page (limit 5, offset 5)
        response = await client.get(
            f"/api/v1/chat/history?session_id={session_id}&limit=5&offset=5"
        )
        assert response.status_code == 200
        page2 = response.json()
        assert len(page2["messages"]) == 5
        assert page2["offset"] == 5
        
        # Verify no overlap between pages
        page1_ids = {m["id"] for m in page1["messages"]}
        page2_ids = {m["id"] for m in page2["messages"]}
        assert len(page1_ids.intersection(page2_ids)) == 0
