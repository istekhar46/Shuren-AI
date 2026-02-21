"""
Integration tests for SchedulerAgent.

This module tests the SchedulerAgent with real database operations,
verifying all tools work correctly with actual data.
"""

import pytest
import pytest_asyncio
from datetime import time
from uuid import uuid4

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.agents.scheduler import SchedulerAgent
from app.agents.context import AgentContext
from app.models.user import User
from app.models.profile import UserProfile
from app.models.preferences import WorkoutSchedule, MealSchedule, HydrationPreference


@pytest_asyncio.fixture
async def user_with_schedules(db_session: AsyncSession) -> tuple[User, UserProfile]:
    """Create a user with workout and meal schedules."""
    from app.core.security import hash_password
    from datetime import datetime, timezone
    
    # Create user
    user = User(
        id=uuid4(),
        email="scheduler_test@example.com",
        hashed_password=hash_password("password123"),
        full_name="Scheduler Test User",
        is_active=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(user)
    
    # Create profile
    profile = UserProfile(
        id=uuid4(),
        user_id=user.id,
        is_locked=True,
        fitness_level="intermediate",
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(profile)
    
    # Create workout schedules (Monday, Wednesday, Friday)
    workout_schedules = [
        WorkoutSchedule(
            id=uuid4(),
            profile_id=profile.id,
            day_of_week=0,  # Monday
            scheduled_time=time(7, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        WorkoutSchedule(
            id=uuid4(),
            profile_id=profile.id,
            day_of_week=2,  # Wednesday
            scheduled_time=time(7, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        WorkoutSchedule(
            id=uuid4(),
            profile_id=profile.id,
            day_of_week=4,  # Friday
            scheduled_time=time(18, 0),
            enable_notifications=False,
            created_at=datetime.now(timezone.utc)
        ),
    ]
    for schedule in workout_schedules:
        db_session.add(schedule)
    
    # Create meal schedules
    meal_schedules = [
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="breakfast",
            scheduled_time=time(8, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="lunch",
            scheduled_time=time(13, 0),
            enable_notifications=True,
            created_at=datetime.now(timezone.utc)
        ),
        MealSchedule(
            id=uuid4(),
            profile_id=profile.id,
            meal_name="dinner",
            scheduled_time=time(19, 30),
            enable_notifications=False,
            created_at=datetime.now(timezone.utc)
        ),
    ]
    for schedule in meal_schedules:
        db_session.add(schedule)
    
    # Create hydration preference
    hydration = HydrationPreference(
        id=uuid4(),
        profile_id=profile.id,
        daily_water_target_ml=3000,
        reminder_frequency_minutes=60,
        enable_notifications=True,
        created_at=datetime.now(timezone.utc)
    )
    db_session.add(hydration)
    
    await db_session.commit()
    await db_session.refresh(user)
    await db_session.refresh(profile)
    
    return user, profile


@pytest.mark.asyncio
class TestSchedulerAgentIntegration:
    """Integration tests for SchedulerAgent with database."""
    
    async def test_agent_initialization(self, user_with_schedules, db_session):
        """Test that SchedulerAgent initializes correctly."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        
        assert agent is not None
        assert agent.context.user_id == str(user.id)
        assert agent.db_session is db_session
        assert len(agent.get_tools()) == 3
    
    async def test_get_upcoming_schedule_tool(self, user_with_schedules, db_session):
        """Test get_upcoming_schedule tool retrieves all schedules."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the get_upcoming_schedule tool
        schedule_tool = next(t for t in tools if t.name == "get_upcoming_schedule")
        
        # Call the tool
        result = await schedule_tool.ainvoke({})
        
        # Verify result
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "workouts" in data["data"]
        assert "meals" in data["data"]
        
        # Verify workout schedules
        workouts = data["data"]["workouts"]
        assert len(workouts) == 3
        assert workouts[0]["day"] == "Monday"
        assert workouts[0]["time"] == "07:00"
        assert workouts[0]["notifications_enabled"] is True
        
        # Verify meal schedules
        meals = data["data"]["meals"]
        assert len(meals) == 3
        assert meals[0]["meal_name"] == "breakfast"
        assert meals[0]["time"] == "08:00"
        assert meals[0]["notifications_enabled"] is True
    
    async def test_reschedule_workout_tool_success(self, user_with_schedules, db_session):
        """Test reschedule_workout tool successfully updates schedule."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Get the Monday workout schedule ID
        stmt = select(WorkoutSchedule).where(
            WorkoutSchedule.profile_id == profile.id,
            WorkoutSchedule.day_of_week == 0
        )
        result = await db_session.execute(stmt)
        monday_schedule = result.scalar_one()
        
        # Find the reschedule_workout tool
        reschedule_tool = next(t for t in tools if t.name == "reschedule_workout")
        
        # Reschedule Monday workout to Tuesday at 18:00
        result = await reschedule_tool.ainvoke({
            "workout_schedule_id": str(monday_schedule.id),
            "new_day_of_week": 1,  # Tuesday
            "new_time": "18:00"
        })
        
        # Verify result
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "Workout rescheduled" in data["data"]["message"]
        assert data["data"]["old_schedule"]["day"] == "Monday"
        assert data["data"]["old_schedule"]["time"] == "07:00"
        assert data["data"]["new_schedule"]["day"] == "Tuesday"
        assert data["data"]["new_schedule"]["time"] == "18:00"
        
        # Verify database was updated
        await db_session.refresh(monday_schedule)
        assert monday_schedule.day_of_week == 1
        assert monday_schedule.scheduled_time == time(18, 0)
    
    async def test_reschedule_workout_conflict_detection(self, user_with_schedules, db_session):
        """Test reschedule_workout detects conflicts."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Get the Monday workout schedule ID
        stmt = select(WorkoutSchedule).where(
            WorkoutSchedule.profile_id == profile.id,
            WorkoutSchedule.day_of_week == 0
        )
        result = await db_session.execute(stmt)
        monday_schedule = result.scalar_one()
        
        # Find the reschedule_workout tool
        reschedule_tool = next(t for t in tools if t.name == "reschedule_workout")
        
        # Try to reschedule Monday workout to Wednesday (where another workout exists)
        result = await reschedule_tool.ainvoke({
            "workout_schedule_id": str(monday_schedule.id),
            "new_day_of_week": 2,  # Wednesday (already has a workout)
            "new_time": "07:00"
        })
        
        # Verify conflict was detected
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert data["error"] == "Conflict detected"
        assert "Another workout is already scheduled" in data["data"]["message"]
    
    async def test_reschedule_workout_invalid_day(self, user_with_schedules, db_session):
        """Test reschedule_workout validates day_of_week."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Get any workout schedule ID
        stmt = select(WorkoutSchedule).where(
            WorkoutSchedule.profile_id == profile.id
        )
        result = await db_session.execute(stmt)
        schedule = result.scalars().first()
        
        # Find the reschedule_workout tool
        reschedule_tool = next(t for t in tools if t.name == "reschedule_workout")
        
        # Try to reschedule with invalid day_of_week
        result = await reschedule_tool.ainvoke({
            "workout_schedule_id": str(schedule.id),
            "new_day_of_week": 8,  # Invalid (must be 0-6)
            "new_time": "18:00"
        })
        
        # Verify error
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Invalid day_of_week" in data["error"]
    
    async def test_reschedule_workout_invalid_time_format(self, user_with_schedules, db_session):
        """Test reschedule_workout validates time format."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Get any workout schedule ID
        stmt = select(WorkoutSchedule).where(
            WorkoutSchedule.profile_id == profile.id
        )
        result = await db_session.execute(stmt)
        schedule = result.scalars().first()
        
        # Find the reschedule_workout tool
        reschedule_tool = next(t for t in tools if t.name == "reschedule_workout")
        
        # Try to reschedule with invalid time format
        result = await reschedule_tool.ainvoke({
            "workout_schedule_id": str(schedule.id),
            "new_day_of_week": 3,
            "new_time": "25:00"  # Invalid hour
        })
        
        # Verify error
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Invalid time format" in data["error"]
    
    async def test_update_reminder_preferences_workout(self, user_with_schedules, db_session):
        """Test update_reminder_preferences for workout reminders."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the update_reminder_preferences tool
        reminder_tool = next(t for t in tools if t.name == "update_reminder_preferences")
        
        # Disable workout reminders
        result = await reminder_tool.ainvoke({
            "reminder_type": "workout",
            "enabled": False
        })
        
        # Verify result
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "Workout reminders disabled" in data["data"]["message"]
        assert data["data"]["updated_count"] == 3  # 3 workout schedules
        
        # Verify database was updated
        stmt = select(WorkoutSchedule).where(
            WorkoutSchedule.profile_id == profile.id
        )
        result = await db_session.execute(stmt)
        schedules = result.scalars().all()
        
        for schedule in schedules:
            assert schedule.enable_notifications is False
    
    async def test_update_reminder_preferences_meal(self, user_with_schedules, db_session):
        """Test update_reminder_preferences for meal reminders."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the update_reminder_preferences tool
        reminder_tool = next(t for t in tools if t.name == "update_reminder_preferences")
        
        # Enable meal reminders (some are already enabled, some disabled)
        result = await reminder_tool.ainvoke({
            "reminder_type": "meal",
            "enabled": True
        })
        
        # Verify result
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "Meal reminders enabled" in data["data"]["message"]
        assert data["data"]["updated_count"] == 3  # 3 meal schedules
        
        # Verify database was updated
        stmt = select(MealSchedule).where(
            MealSchedule.profile_id == profile.id
        )
        result = await db_session.execute(stmt)
        schedules = result.scalars().all()
        
        for schedule in schedules:
            assert schedule.enable_notifications is True
    
    async def test_update_reminder_preferences_hydration(self, user_with_schedules, db_session):
        """Test update_reminder_preferences for hydration reminders."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the update_reminder_preferences tool
        reminder_tool = next(t for t in tools if t.name == "update_reminder_preferences")
        
        # Disable hydration reminders
        result = await reminder_tool.ainvoke({
            "reminder_type": "hydration",
            "enabled": False
        })
        
        # Verify result
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert "Hydration reminders disabled" in data["data"]["message"]
        assert data["data"]["updated_count"] == 1  # 1 hydration preference
        
        # Verify database was updated
        stmt = select(HydrationPreference).where(
            HydrationPreference.profile_id == profile.id
        )
        result = await db_session.execute(stmt)
        hydration = result.scalar_one()
        
        assert hydration.enable_notifications is False
    
    async def test_update_reminder_preferences_invalid_type(self, user_with_schedules, db_session):
        """Test update_reminder_preferences validates reminder type."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the update_reminder_preferences tool
        reminder_tool = next(t for t in tools if t.name == "update_reminder_preferences")
        
        # Try with invalid reminder type
        result = await reminder_tool.ainvoke({
            "reminder_type": "invalid_type",
            "enabled": True
        })
        
        # Verify error
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Invalid reminder_type" in data["error"]
    
    async def test_system_prompt_includes_context(self, user_with_schedules, db_session):
        """Test that system prompt includes user context."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="advanced",
            primary_goal="fat_loss",
            energy_level="low",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        
        # Get text mode prompt
        text_prompt = agent._system_prompt(voice_mode=False)
        
        assert "advanced" in text_prompt
        assert "fat_loss" in text_prompt
        assert "scheduling" in text_prompt.lower()
        assert "markdown" in text_prompt.lower()
        
        # Get voice mode prompt
        voice_prompt = agent._system_prompt(voice_mode=True)
        
        assert "advanced" in voice_prompt
        assert "fat_loss" in voice_prompt
        assert "concise" in voice_prompt.lower()
        assert "75 words" in voice_prompt.lower()
    
    async def test_all_tools_have_proper_schemas(self, user_with_schedules, db_session):
        """Test that all tools have proper argument schemas."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        assert len(tools) == 3
        
        for tool in tools:
            assert tool.name is not None
            assert tool.description is not None
            assert hasattr(tool, 'args_schema')
            
            # Verify tool names
            assert tool.name in [
                "get_upcoming_schedule",
                "reschedule_workout",
                "update_reminder_preferences"
            ]
    
    async def test_agent_without_database_session(self, user_with_schedules):
        """Test agent behavior when database session is not provided."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        # Create agent without db_session
        agent = SchedulerAgent(context=context, db_session=None)
        tools = agent.get_tools()
        
        # Find the get_upcoming_schedule tool
        schedule_tool = next(t for t in tools if t.name == "get_upcoming_schedule")
        
        # Call the tool (should handle missing db_session gracefully)
        result = await schedule_tool.ainvoke({})
        
        # Verify error handling
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Database session not available" in data["error"]


@pytest.mark.asyncio
class TestSchedulerAgentEdgeCases:
    """Test edge cases and error scenarios."""
    
    async def test_reschedule_nonexistent_workout(self, user_with_schedules, db_session):
        """Test rescheduling a workout that doesn't exist."""
        user, profile = user_with_schedules
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="intermediate",
            primary_goal="muscle_gain",
            energy_level="high",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the reschedule_workout tool
        reschedule_tool = next(t for t in tools if t.name == "reschedule_workout")
        
        # Try to reschedule with non-existent ID
        result = await reschedule_tool.ainvoke({
            "workout_schedule_id": str(uuid4()),  # Random UUID
            "new_day_of_week": 3,
            "new_time": "18:00"
        })
        
        # Verify error
        import json
        data = json.loads(result)
        
        assert data["success"] is False
        assert "Workout schedule not found" in data["error"]
    
    async def test_update_reminders_for_user_without_hydration(self, db_session):
        """Test updating hydration reminders when user has no hydration preference."""
        from app.core.security import hash_password
        from datetime import datetime, timezone
        
        # Create user without hydration preference
        user = User(
            id=uuid4(),
            email="no_hydration@example.com",
            hashed_password=hash_password("password123"),
            full_name="No Hydration User",
            is_active=True,
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(user)
        
        profile = UserProfile(
            id=uuid4(),
            user_id=user.id,
            is_locked=True,
            fitness_level="beginner",
            created_at=datetime.now(timezone.utc)
        )
        db_session.add(profile)
        
        await db_session.commit()
        
        context = AgentContext(
            user_id=str(user.id),
            fitness_level="beginner",
            primary_goal="general_fitness",
            energy_level="medium",
            conversation_history=[]
        )
        
        agent = SchedulerAgent(context=context, db_session=db_session)
        tools = agent.get_tools()
        
        # Find the update_reminder_preferences tool
        reminder_tool = next(t for t in tools if t.name == "update_reminder_preferences")
        
        # Try to update hydration reminders
        result = await reminder_tool.ainvoke({
            "reminder_type": "hydration",
            "enabled": True
        })
        
        # Verify result (should succeed with 0 updates)
        import json
        data = json.loads(result)
        
        assert data["success"] is True
        assert data["data"]["updated_count"] == 0
