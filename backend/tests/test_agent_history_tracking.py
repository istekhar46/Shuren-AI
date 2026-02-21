"""Tests for agent routing history tracking in onboarding."""

import pytest
from uuid import uuid4

from app.models.onboarding import OnboardingState
from app.models.user import User
from app.services.onboarding_service import OnboardingService


@pytest.mark.asyncio
class TestAgentHistoryTracking:
    """Test agent routing history tracking functionality."""
    
    async def test_agent_history_recorded_on_state_change(self, db_session, test_user):
        """Test that agent_history is recorded when state advances."""
        service = OnboardingService(db_session)
        
        # Save state 1 with agent context
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "beginner"},
            agent_type="workout_planning"
        )
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Verify agent_history was recorded
        assert state.agent_history is not None
        assert len(state.agent_history) == 1
        
        history_entry = state.agent_history[0]
        assert history_entry["state"] == 1
        assert history_entry["agent"] == "workout_planning"
        assert history_entry["previous_state"] == 0
        assert "timestamp" in history_entry
    
    async def test_agent_history_tracks_multiple_states(self, db_session, test_user):
        """Test that agent_history tracks multiple state transitions."""
        service = OnboardingService(db_session)
        
        # Save multiple states with different agents
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "intermediate"},
            agent_type="workout_planning"
        )
        
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=2,
            data={"goals": [{"goal_type": "muscle_gain"}]},
            agent_type="workout_planning"
        )
        
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=3,
            data={
                "equipment": ["dumbbells"],
                "injuries": [],
                "limitations": []
            },
            agent_type="workout_planning"
        )
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Verify all transitions were recorded
        assert len(state.agent_history) == 3
        
        # Check first transition
        assert state.agent_history[0]["state"] == 1
        assert state.agent_history[0]["agent"] == "workout_planning"
        assert state.agent_history[0]["previous_state"] == 0
        
        # Check second transition
        assert state.agent_history[1]["state"] == 2
        assert state.agent_history[1]["agent"] == "workout_planning"
        assert state.agent_history[1]["previous_state"] == 1
        
        # Check third transition
        assert state.agent_history[2]["state"] == 3
        assert state.agent_history[2]["agent"] == "workout_planning"
        assert state.agent_history[2]["previous_state"] == 2
    
    async def test_agent_history_not_recorded_without_agent_type(self, db_session, test_user):
        """Test that agent_history is not recorded when agent_type is None."""
        service = OnboardingService(db_session)
        
        # Save state without agent context
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "beginner"},
            agent_type=None
        )
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Verify agent_history is empty
        assert state.agent_history == []
    
    async def test_agent_history_not_recorded_when_state_not_advancing(self, db_session, test_user):
        """Test that agent_history is not recorded when updating existing state."""
        service = OnboardingService(db_session)
        
        # Save state 1
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "beginner"},
            agent_type="workout_planning"
        )
        
        # Update state 1 (not advancing)
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "intermediate"},
            agent_type="workout_planning"
        )
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Verify only one history entry (from first save)
        assert len(state.agent_history) == 1
        assert state.agent_history[0]["state"] == 1
    
    async def test_agent_history_tracks_different_agents(self, db_session, test_user):
        """Test that agent_history correctly tracks different agent types."""
        service = OnboardingService(db_session)
        
        # Workout agent handles states 1-3
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "beginner"},
            agent_type="workout_planning"
        )
        
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=2,
            data={"goals": [{"goal_type": "fat_loss"}]},
            agent_type="workout_planning"
        )
        
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=3,
            data={
                "equipment": ["bodyweight"],
                "injuries": [],
                "limitations": []
            },
            agent_type="workout_planning"
        )
        
        # Diet agent handles state 4
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=4,
            data={
                "diet_type": "vegetarian",
                "allergies": [],
                "intolerances": [],
                "dislikes": []
            },
            agent_type="diet_planning"
        )
        
        # Get onboarding state
        state = await service.get_onboarding_state(test_user.id)
        
        # Verify agent types are tracked correctly
        assert len(state.agent_history) == 4
        assert state.agent_history[0]["agent"] == "workout_planning"
        assert state.agent_history[1]["agent"] == "workout_planning"
        assert state.agent_history[2]["agent"] == "workout_planning"
        assert state.agent_history[3]["agent"] == "diet_planning"
    
    async def test_agent_history_persists_across_sessions(self, db_session, test_user):
        """Test that agent_history persists in database across sessions."""
        service = OnboardingService(db_session)
        
        # Save state with agent context
        await service.save_onboarding_step(
            user_id=test_user.id,
            step=1,
            data={"fitness_level": "advanced"},
            agent_type="workout_planning"
        )
        
        # Commit and refresh
        await db_session.commit()
        
        # Create new service instance (simulating new session)
        new_service = OnboardingService(db_session)
        state = await new_service.get_onboarding_state(test_user.id)
        
        # Verify history persisted
        assert len(state.agent_history) == 1
        assert state.agent_history[0]["agent"] == "workout_planning"
